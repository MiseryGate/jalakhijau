import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import json
import uuid

# Initialize Faker for Indonesian locale
fake = Faker('id_ID')

def load_company_data(pt_csv_file):
    """Load PT company data to link transactions"""
    try:
        df = pd.read_csv(pt_csv_file)
        return df.to_dict('records')
    except:
        # Fallback if PT data not ready yet
        return generate_dummy_companies()

def generate_dummy_companies():
    """Fallback company data if PT CSV not available"""
    palm_companies = [
        'PT BERKAH SAWIT NUSANTARA', 'PT HIJAU SEJAHTERA ABADI', 
        'PT CAHAYA PALM OIL', 'PT DUTA KELAPA SAWIT',
        'PT EMAS HIJAU PLANTATION', 'PT FAJAR SAWIT MANDIRI'
    ]
    
    shell_companies = [
        'PT KARYA UTAMA CONSULTING', 'PT PRIMA JAYA TRADING',
        'PT OMEGA DIGITAL SOLUTIONS', 'PT NUSA BERKAH MANDIRI',
        'PT GEMILANG MULTI FINANCE', 'PT CAHAYA INVESTAMA'
    ]
    
    companies = []
    for i, name in enumerate(palm_companies + shell_companies):
        companies.append({
            'company_id': f'{"PALM" if i < len(palm_companies) else "SHELL"}_{i+1:03d}',
            'nama_perseroan': name,
            'npwp_perusahaan': generate_npwp(),
            'is_suspicious': i >= len(palm_companies),  # Shell companies are suspicious
            'risk_score': random.randint(70, 95) if i >= len(palm_companies) else random.randint(20, 50)
        })
    
    return companies

def generate_npwp():
    """Generate realistic but fake NPWP"""
    part1 = f"{random.randint(10, 99)}"
    part2 = f"{random.randint(100, 999)}"
    part3 = f"{random.randint(100, 999)}"
    part4 = f"{random.randint(1, 9)}"
    part5 = f"{random.randint(100, 999)}"
    part6 = f"{random.randint(100, 999)}"
    return f"{part1}.{part2}.{part3}.{part4}-{part5}.{part6}"

def generate_account_number():
    """Generate realistic Indonesian bank account numbers"""
    bank_codes = ['008', '009', '011', '013', '014', '016', '019', '022']  # Major Indonesian banks
    account_num = f"{random.choice(bank_codes)}{random.randint(1000000000, 9999999999)}"
    return account_num

def generate_transaction_types():
    """Define transaction types and their characteristics"""
    return {
        'legitimate': {
            'types': ['SALARY_PAYMENT', 'SUPPLIER_PAYMENT', 'TAX_PAYMENT', 'UTILITY_PAYMENT', 'LOAN_PAYMENT'],
            'amounts': (1000000, 50000000),  # 1M - 50M IDR
            'frequency': 0.7  # 70% of transactions
        },
        'suspicious_structuring': {
            'types': ['CASH_DEPOSIT', 'TRANSFER', 'WITHDRAWAL'],
            'amounts': (45000000, 49900000),  # Just under 50M reporting threshold
            'frequency': 0.15  # 15% of transactions
        },
        'suspicious_large': {
            'types': ['LARGE_TRANSFER', 'FOREIGN_EXCHANGE', 'INVESTMENT'],
            'amounts': (100000000, 5000000000),  # 100M - 5B IDR
            'frequency': 0.1  # 10% of transactions
        },
        'layering': {
            'types': ['INTER_COMPANY_TRANSFER', 'LOAN_ADVANCE', 'CAPITAL_INJECTION'],
            'amounts': (500000000, 2000000000),  # 500M - 2B IDR
            'frequency': 0.05  # 5% of transactions
        }
    }

def generate_individuals(count=200):
    """Generate individual account holders (for personal transactions)"""
    individuals = []
    
    first_names = ['Ahmad', 'Budi', 'Sari', 'Dewi', 'Eko', 'Fitri', 'Gina', 'Hadi', 'Indra', 'Joko']
    last_names = ['Wijaya', 'Kusuma', 'Pratama', 'Sari', 'Putra', 'Santoso', 'Wibowo', 'Gunawan']
    
    for i in range(count):
        full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        individuals.append({
            'person_id': f'IND_{i+1:04d}',
            'full_name': full_name,
            'nik': generate_nik(),
            'npwp': generate_npwp(),
            'account_number': generate_account_number(),
            'is_nominee': random.random() < 0.2  # 20% are potential nominees
        })
    
    return individuals

def generate_nik():
    """Generate realistic but fake NIK (16 digits)"""
    area_codes = ['3201', '3273', '3174', '6471', '1871', '3578']
    area = random.choice(area_codes)
    birth_date = fake.date_of_birth(minimum_age=25, maximum_age=70)
    dd = birth_date.strftime('%d')
    mm = birth_date.strftime('%m')
    yy = birth_date.strftime('%y')
    seq = f"{random.randint(1, 9999):04d}"
    return f"{area}{dd}{mm}{yy}{seq}"

def create_transaction_network(companies, individuals, num_transactions=5000):
    """Create realistic transaction networks with suspicious patterns"""
    
    transactions = []
    transaction_types = generate_transaction_types()
    
    # Separate companies by type
    palm_companies = [c for c in companies if not c.get('is_suspicious', False)]
    shell_companies = [c for c in companies if c.get('is_suspicious', False)]
    nominees = [p for p in individuals if p.get('is_nominee', False)]
    regular_people = [p for p in individuals if not p.get('is_nominee', False)]
    
    # Generate transactions over 12 months
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(num_transactions):
        # Determine transaction pattern
        rand = random.random()
        
        if rand < 0.4:  # 40% Normal business transactions
            pattern_type = 'legitimate'
            sender = random.choice(palm_companies + regular_people)
            receiver = random.choice(palm_companies + regular_people)
            
        elif rand < 0.6:  # 20% Suspicious structuring (just under reporting limits)
            pattern_type = 'suspicious_structuring'
            sender = random.choice(palm_companies)
            receiver = random.choice(shell_companies + nominees)
            
        elif rand < 0.8:  # 20% Large suspicious transfers
            pattern_type = 'suspicious_large'
            sender = random.choice(palm_companies)
            receiver = random.choice(shell_companies)
            
        else:  # 20% Complex layering schemes
            pattern_type = 'layering'
            if random.random() < 0.5:
                sender = random.choice(shell_companies)
                receiver = random.choice(shell_companies + nominees)
            else:
                sender = random.choice(palm_companies)
                receiver = random.choice(shell_companies)
        
        # Generate transaction details
        txn_config = transaction_types[pattern_type]
        amount = random.randint(*txn_config['amounts'])
        txn_type = random.choice(txn_config['types'])
        
        # Generate realistic date (with clustering around palm harvest seasons)
        if pattern_type in ['suspicious_large', 'layering']:
            # Suspicious transactions clustered around harvest months (Mar-Apr, Sep-Oct)
            if random.random() < 0.6:
                month = random.choice([3, 4, 9, 10])
                day = random.randint(1, 28)
                year = random.choice([2023, 2024])
                txn_date = datetime(year, month, day) + timedelta(
                    hours=random.randint(8, 18),
                    minutes=random.randint(0, 59)
                )
            else:
                txn_date = fake.date_time_between(start_date=start_date, end_date=datetime.now())
        else:
            txn_date = fake.date_time_between(start_date=start_date, end_date=datetime.now())
        
        # Determine account numbers
        if 'company_id' in sender:
            sender_account = f"CORP_{sender['company_id']}_001"
            sender_name = sender['nama_perseroan']
            sender_npwp = sender['npwp_perusahaan']
        else:
            sender_account = sender['account_number']
            sender_name = sender['full_name']
            sender_npwp = sender['npwp']
            
        if 'company_id' in receiver:
            receiver_account = f"CORP_{receiver['company_id']}_001"
            receiver_name = receiver['nama_perseroan']
            receiver_npwp = receiver['npwp_perusahaan']
        else:
            receiver_account = receiver['account_number']
            receiver_name = receiver['full_name']
            receiver_npwp = receiver['npwp']
        
        # Calculate risk score
        risk_score = calculate_transaction_risk(
            amount, txn_type, pattern_type, 
            sender.get('risk_score', 10), 
            receiver.get('risk_score', 10)
        )
        
        # Generate transaction record
        transaction = {
            'transaction_id': f'TXN_{i+1:06d}',
            'transaction_date': txn_date.strftime('%Y-%m-%d %H:%M:%S'),
            'sender_account': sender_account,
            'sender_name': sender_name,
            'sender_npwp': sender_npwp,
            'receiver_account': receiver_account,
            'receiver_name': receiver_name,
            'receiver_npwp': receiver_npwp,
            'amount_idr': amount,
            'transaction_type': txn_type,
            'description': generate_transaction_description(txn_type, sender_name, receiver_name),
            'bank_code': random.choice(['008', '009', '011', '013', '014']),
            'channel': random.choice(['INTERNET_BANKING', 'MOBILE_BANKING', 'ATM', 'BRANCH', 'RTGS']),
            'currency': 'IDR',
            'pattern_type': pattern_type,
            'risk_score': risk_score,
            'is_flagged': risk_score > 70,
            'reporting_threshold_flag': amount >= 50000000,  # 50M IDR threshold
            'cross_border': random.random() < 0.1 if pattern_type in ['suspicious_large', 'layering'] else False
        }
        
        transactions.append(transaction)
    
    return transactions

def calculate_transaction_risk(amount, txn_type, pattern_type, sender_risk, receiver_risk):
    """Calculate risk score for transaction"""
    base_score = 0
    
    # Amount-based risk
    if amount >= 1000000000:  # > 1B IDR
        base_score += 30
    elif amount >= 500000000:  # > 500M IDR
        base_score += 20
    elif 45000000 <= amount < 50000000:  # Just under reporting threshold
        base_score += 25
    
    # Transaction type risk
    type_risk = {
        'CASH_DEPOSIT': 25, 'LARGE_TRANSFER': 20, 'FOREIGN_EXCHANGE': 30,
        'INTER_COMPANY_TRANSFER': 15, 'INVESTMENT': 10,
        'SALARY_PAYMENT': 0, 'SUPPLIER_PAYMENT': 5, 'TAX_PAYMENT': 0
    }
    base_score += type_risk.get(txn_type, 10)
    
    # Pattern-based risk
    pattern_risk = {
        'legitimate': 0, 'suspicious_structuring': 40, 
        'suspicious_large': 35, 'layering': 45
    }
    base_score += pattern_risk.get(pattern_type, 0)
    
    # Entity risk (average of sender and receiver)
    entity_risk = (sender_risk + receiver_risk) / 4  # Scaled down
    base_score += entity_risk
    
    return min(int(base_score), 100)

def generate_transaction_description(txn_type, sender, receiver):
    """Generate realistic transaction descriptions"""
    descriptions = {
        'SALARY_PAYMENT': f'Pembayaran gaji karyawan dari {sender}',
        'SUPPLIER_PAYMENT': f'Pembayaran supplier untuk {receiver}',
        'TAX_PAYMENT': f'Pembayaran pajak perusahaan',
        'CASH_DEPOSIT': f'Setoran tunai ke rekening perusahaan',
        'LARGE_TRANSFER': f'Transfer dana operasional ke {receiver}',
        'FOREIGN_EXCHANGE': f'Transaksi valuta asing untuk ekspor',
        'INTER_COMPANY_TRANSFER': f'Transfer antar perusahaan grup',
        'LOAN_ADVANCE': f'Pinjaman/advance kepada {receiver}',
        'INVESTMENT': f'Investasi/penyertaan modal',
        'CAPITAL_INJECTION': f'Penambahan modal perusahaan'
    }
    
    return descriptions.get(txn_type, f'Transfer dari {sender} ke {receiver}')

def create_suspicious_transaction_clusters(transactions):
    """Create clusters of related suspicious transactions (for network analysis)"""
    
    suspicious_txns = [t for t in transactions if t['risk_score'] > 60]
    clusters = []
    
    # Group by entities involved in multiple suspicious transactions
    entity_groups = {}
    
    for txn in suspicious_txns:
        sender = txn['sender_npwp']
        receiver = txn['receiver_npwp']
        
        # Group by sender
        if sender not in entity_groups:
            entity_groups[sender] = []
        entity_groups[sender].append(txn)
        
        # Group by receiver
        if receiver not in entity_groups:
            entity_groups[receiver] = []
        entity_groups[receiver].append(txn)
    
    # Create clusters for entities with multiple suspicious transactions
    cluster_id = 1
    for entity, txns in entity_groups.items():
        if len(txns) >= 3:  # Entity involved in 3+ suspicious transactions
            cluster = {
                'cluster_id': f'CLUSTER_{cluster_id:03d}',
                'primary_entity': entity,
                'transaction_count': len(txns),
                'total_amount': sum(t['amount_idr'] for t in txns),
                'date_range': {
                    'start': min(t['transaction_date'] for t in txns),
                    'end': max(t['transaction_date'] for t in txns)
                },
                'transaction_ids': [t['transaction_id'] for t in txns],
                'avg_risk_score': sum(t['risk_score'] for t in txns) / len(txns),
                'pattern_analysis': analyze_transaction_patterns(txns)
            }
            clusters.append(cluster)
            cluster_id += 1
    
    return clusters

def analyze_transaction_patterns(transactions):
    """Analyze patterns in a group of transactions"""
    patterns = []
    
    amounts = [t['amount_idr'] for t in transactions]
    dates = [datetime.strptime(t['transaction_date'], '%Y-%m-%d %H:%M:%S') for t in transactions]
    
    # Check for structuring (amounts just under thresholds)
    structuring_count = sum(1 for amt in amounts if 45000000 <= amt < 50000000)
    if structuring_count >= 2:
        patterns.append('STRUCTURING_DETECTED')
    
    # Check for rapid succession (multiple transactions within 24 hours)
    dates.sort()
    rapid_succession = 0
    for i in range(1, len(dates)):
        if (dates[i] - dates[i-1]).total_seconds() < 86400:  # < 24 hours
            rapid_succession += 1
    
    if rapid_succession >= 2:
        patterns.append('RAPID_SUCCESSION')
    
    # Check for round amounts (potential artificial transactions)
    round_amounts = sum(1 for amt in amounts if amt % 1000000 == 0)  # Multiples of 1M
    if round_amounts / len(amounts) > 0.5:
        patterns.append('ROUND_AMOUNTS')
    
    return patterns

def save_transaction_data(transactions, clusters, individuals, base_filename='jalak_hijau_transactions'):
    """Save transaction data in multiple formats"""
    
    # Main transactions CSV
    df_transactions = pd.DataFrame(transactions)
    df_transactions.to_csv(f'{base_filename}.csv', index=False)
    
    # High-risk transactions only
    high_risk_txns = [t for t in transactions if t['risk_score'] > 70]
    df_high_risk = pd.DataFrame(high_risk_txns)
    df_high_risk.to_csv(f'{base_filename}_high_risk.csv', index=False)
    
    # Suspicious clusters
    df_clusters = pd.DataFrame(clusters)
    df_clusters.to_csv(f'{base_filename}_clusters.csv', index=False)
    
    # Individual accounts
    df_individuals = pd.DataFrame(individuals)
    df_individuals.to_csv(f'{base_filename}_individuals.csv', index=False)
    
    # Summary statistics
    summary = {
        'total_transactions': len(transactions),
        'high_risk_transactions': len(high_risk_txns),
        'total_amount_idr': sum(t['amount_idr'] for t in transactions),
        'suspicious_clusters': len(clusters),
        'flagged_transactions': len([t for t in transactions if t['is_flagged']]),
        'cross_border_transactions': len([t for t in transactions if t['cross_border']]),
        'average_risk_score': sum(t['risk_score'] for t in transactions) / len(transactions),
        'date_range': {
            'earliest': min(t['transaction_date'] for t in transactions),
            'latest': max(t['transaction_date'] for t in transactions)
        }
    }
    
    with open(f'{base_filename}_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"Generated {len(transactions)} transactions:")
    print(f"- High-risk transactions: {len(high_risk_txns)} ({len(high_risk_txns)/len(transactions)*100:.1f}%)")
    print(f"- Suspicious clusters: {len(clusters)}")
    print(f"- Total transaction value: Rp {sum(t['amount_idr'] for t in transactions):,.0f}")
    print(f"- Average risk score: {summary['average_risk_score']:.1f}")
    print(f"\nFiles saved:")
    print(f"- {base_filename}.csv (all transactions)")
    print(f"- {base_filename}_high_risk.csv (risk score > 70)")
    print(f"- {base_filename}_clusters.csv (suspicious patterns)")
    print(f"- {base_filename}_individuals.csv (individual accounts)")
    print(f"- {base_filename}_summary.json (statistics)")

def main():
    """Main function to generate all transaction data"""
    print("🚀 Generating JALAK-HIJAU synthetic transaction data...")
    
    # Load company data (or use dummy data)
    try:
        companies = load_company_data('jalak_hijau_pt_data.csv')
        print(f"✅ Loaded {len(companies)} companies from PT data")
    except:
        companies = generate_dummy_companies()
        print(f"⚠️  Using dummy company data ({len(companies)} companies)")
    
    # Generate individual accounts
    individuals = generate_individuals(200)
    print(f"✅ Generated {len(individuals)} individual accounts")
    
    # Generate transaction network
    transactions = create_transaction_network(companies, individuals, num_transactions=8000)
    print(f"✅ Generated {len(transactions)} transactions")
    
    # Create suspicious clusters
    clusters = create_suspicious_transaction_clusters(transactions)
    print(f"✅ Identified {len(clusters)} suspicious clusters")
    
    # Save all data
    save_transaction_data(transactions, clusters, individuals)
    print("🎉 Transaction data generation complete!")
    
    # Display sample high-risk transactions
    high_risk_sample = [t for t in transactions if t['risk_score'] > 85][:3]
    print(f"\n🚨 Sample high-risk transactions:")
    for txn in high_risk_sample:
        print(f"- {txn['transaction_id']}: Rp {txn['amount_idr']:,.0f} "
              f"({txn['sender_name']} → {txn['receiver_name']}) "
              f"Risk: {txn['risk_score']}")

if __name__ == "__main__":
    main()