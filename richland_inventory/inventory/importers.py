# inventory/importers.py

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from openpyxl import load_workbook

from django.db import transaction
from django.utils import timezone

from .models import HydraulicSow, POSSale, CustomerPayment

def _read_file_to_dicts(file_obj):
    """
    Reads a CSV or XLSX file and returns a list of dictionaries.
    Normalizes headers to lowercase_with_underscores.
    """
    data = []
    file_name = file_obj.name.lower()
    
    try:
        if file_name.endswith('.csv'):
            # Use StringIO to handle in-memory file and utf-8-sig to handle BOM
            decoded_file = file_obj.read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(decoded_file)
            # Normalize headers
            reader.fieldnames = [name.strip().lower().replace(' ', '_') for name in reader.fieldnames]
            data = list(reader)
        elif file_name.endswith('.xlsx'):
            wb = load_workbook(file_obj, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if rows and len(rows) > 1:
                headers = [str(h).strip().lower().replace(' ', '_') if h else '' for h in rows[0]]
                for row in rows[1:]:
                    # Create dict, converting None to empty string to mimic CSV behavior
                    row_dict = {headers[i]: (str(val) if val is not None else '') for i, val in enumerate(row) if i < len(headers)}
                    data.append(row_dict)
    except Exception as e:
        # Return an error that can be caught by the view
        raise ValueError(f"Could not read the file. It might be corrupted or in an unsupported format. Error: {e}")
        
    return data

def import_ledger_entries_from_file(file_obj, customer, user):
    """
    Processes an uploaded file (CSV or XLSX) to import ledger entries.
    Expected headers: date, reference, description, charge, payment
    Returns (success_count_charges, success_count_payments, errors_list)
    """
    try:
        data = _read_file_to_dicts(file_obj)
    except ValueError as e:
        return 0, 0, [str(e)]

    if not data:
        return 0, 0, ["File is empty or does not contain data rows."]

    count_charges = 0
    count_payments = 0
    errors = []

    try:
        with transaction.atomic():
            for i, row in enumerate(data, start=2): # Start at 2 for row number in file
                try:
                    # 1. Parse Date
                    date_val = row.get('date')
                    txn_date = None
                    if isinstance(date_val, datetime):
                        txn_date = date_val
                    elif date_val:
                        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y'):
                            try:
                                txn_date = datetime.strptime(str(date_val).split(' ')[0], fmt)
                                break
                            except ValueError:
                                continue
                    
                    if not txn_date:
                        errors.append(f"Row {i}: Invalid or missing date '{date_val}'. Use YYYY-MM-DD format.")
                        continue
                    
                    if not timezone.is_aware(txn_date):
                        txn_date = timezone.make_aware(txn_date)

                    ref = row.get('reference', '').strip()
                    desc = row.get('description', '').strip()

                    # 2. Parse Amounts
                    charge_val = Decimal(row.get('charge') or 0)
                    payment_val = Decimal(row.get('payment') or 0)

                    if charge_val < 0 or payment_val < 0:
                        errors.append(f"Row {i}: Charge and Payment values cannot be negative.")
                        continue

                    if charge_val > 0 and payment_val > 0:
                        errors.append(f"Row {i}: A single entry cannot be both a charge and a payment.")
                        continue

                    # 3. Handle CHARGE (Debit)
                    if charge_val > 0:
                        if not ref:
                            errors.append(f"Row {i}: 'reference' is required for charges.")
                            continue
                        if POSSale.objects.filter(receipt_id=ref).exists():
                            errors.append(f"Row {i}: A charge with reference '{ref}' already exists.")
                            continue
                        
                        POSSale.objects.create(
                            receipt_id=ref, customer=customer, payment_method='CREDIT',
                            total_amount=charge_val, amount_paid=0, change_given=0,
                            timestamp=txn_date, notes=desc or f"Imported Charge from file.",
                            cashier=user
                        )
                        count_charges += 1

                    # 4. Handle PAYMENT (Credit)
                    elif payment_val > 0:
                        CustomerPayment.objects.create(
                            customer=customer, amount=payment_val, payment_date=txn_date,
                            reference_number=ref, notes=desc or f"Imported Payment from file.",
                            recorded_by=user
                        )
                        count_payments += 1

                except (InvalidOperation, ValueError) as e:
                    errors.append(f"Row {i}: Invalid number format for charge/payment. Details: {e}")
                
            if errors:
                raise ValueError("Errors found during processing. Rolling back changes.")

    except ValueError:
        return 0, 0, errors
    except Exception as e:
        return 0, 0, [f"An unexpected error occurred: {e}"]

    return count_charges, count_payments, []


def import_sow_from_file(file_obj, customer, user):
    """
    Processes an uploaded file (CSV or XLSX) to import SOW records.
    Returns (success_count, errors_list)
    """
    try:
        data = _read_file_to_dicts(file_obj)
    except ValueError as e:
        return 0, [str(e)]
        
    if not data:
        return 0, ["File is empty or does not contain data rows."]

    count = 0
    errors = []

    try:
        with transaction.atomic():
            for i, row in enumerate(data, start=2):
                try:
                    cost_val = row.get('cost', '0').strip()
                    cost = Decimal(cost_val) if cost_val else Decimal('0.00')

                    if not row.get('hose_type'):
                        errors.append(f"Row {i}: 'hose_type' is a required field.")
                        continue

                    HydraulicSow.objects.create(
                        customer=customer, created_by=user, hose_type=row.get('hose_type', ''),
                        diameter=row.get('diameter', ''), length=row.get('length') or None,
                        pressure=row.get('pressure') or None, cost=cost if cost > 0 else None,
                        application=row.get('application', ''), fitting_a=row.get('fitting_a', ''),
                        fitting_b=row.get('fitting_b', ''), notes=row.get('notes', '')
                    )
                    count += 1
                except (InvalidOperation, ValueError) as e:
                    errors.append(f"Row {i}: Invalid number format for cost/length/pressure. Details: {e}")
            
            if errors:
                raise ValueError("Errors found during processing. Rolling back changes.")

    except ValueError:
        return 0, errors
    except Exception as e:
        return 0, [f"An unexpected error occurred: {e}"]

    return count, []