import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import uuid

# Initialize Faker for Indonesian locale
fake = Faker('id_ID')

def load_palm_companies(csv_file):
    """Load existing palm oil company data"""
    df = pd.read_csv(csv_file)
    return df['company'].dropna().unique().tolist()

def generate_kbli_codes():
    """Generate relevant KBLI codes for palm oil and related industries"""
    palm_related_kbli = [
        '01134',  # Budidaya kelapa sawit
        '01135',  # Budidaya kelapa
        '10411',  # Industri minyak kelapa sawit kasar
        '10412',  # Industri minyak kelapa sawit olahan
        '46691',  # Perdagangan besar minyak nabati
        '02200',  # Penebangan kayu
        '08910',  # Pertambangan mineral lainnya
        '68100',  # Kegiatan real estat dengan hak milik sendiri
        '70200',  # Konsultasi manajemen
        '82990',  # Aktivitas jasa penunjang usaha lainnya
    ]
    
    # Add some unrelated KBLI for shell companies
    unrelated_kbli = [
        '47911',  # Perdagangan eceran melalui internet
        '58190',  # Penerbitan lainnya
        '62010',  # Aktivitas pemrograman komputer
        '64199',  # Aktivitas jasa keuangan lainnya
        '77100',  # Sewa menyewa kendaraan bermotor
    ]
    
    return palm_related_kbli + unrelated_kbli

def generate_suspicious_company_names():
    """Generate typical shell/front company names"""
    prefixes = ['CV', 'PT', 'UD']
    suspicious_patterns = [
        'BERKAH NUSANTARA',
        'CAHAYA MANDIRI', 
        'DUTA SEJAHTERA',
        'EMAS KENCANA',
        'FAJAR CEMERLANG',
        'GEMILANG ABADI',
        'HARAPAN BARU',
        'INDAH PERMAI',
        'JAYA MAKMUR',
        'KARYA UTAMA',
        'LESTARI MANDIRI',
        'MAJU BERSAMA',
        'NUSA INDAH',
        'OMEGA PRIMA',
        'PRIMA SEJAHTERA'
    ]
    
    return [f"{random.choice(prefixes)} {name}" for name in suspicious_patterns]

def generate_indonesian_names(count):
    """Generate realistic Indonesian personal names"""
    first_names = ['Ahmad', 'Budi', 'Sari', 'Dewi', 'Eko', 'Fitri', 'Gina', 'Hadi', 'Indra', 'Joko', 
                   'Kartika', 'Linda', 'Maya', 'Nana', 'Oki', 'Putra', 'Ratna', 'Sinta', 'Tono', 'Umar',
                   'Vina', 'Wati', 'Yudi', 'Zaki', 'Andi', 'Bayu', 'Citra', 'Dian', 'Endang', 'Farid']
    
    last_names = ['Wijaya', 'Kusuma', 'Pratama', 'Sari', 'Putra', 'Putri', 'Santoso', 'Wibowo', 'Setiawan',
                  'Hartono', 'Gunawan', 'Firmansyah', 'Hidayat', 'Rachmadi', 'Wahyudi', 'Permana', 'Nugroho',
                  'Budiman', 'Hakim', 'Rahman', 'Kurniawan', 'Maulana', 'Syahputra', 'Wardana', 'Darmawan']
    
    names = []
    for _ in range(count):
        first = random.choice(first_names)
        last = random.choice(last_names)
        names.append(f"{first} {last}")
    
    return names

def generate_nik():
    """Generate realistic but fake NIK (16 digits)"""
    # First 6: area code (realistic Indonesian area codes)
    area_codes = ['3201', '3273', '3174', '6471', '1871', '3578', '3471', '3215']
    area = random.choice(area_codes)
    
    # Next 6: birth date (DDMMYY)
    birth_date = fake.date_of_birth(minimum_age=25, maximum_age=70)
    dd = birth_date.strftime('%d')
    mm = birth_date.strftime('%m')
    yy = birth_date.strftime('%y')
    
    # Last 4: sequence number
    seq = f"{random.randint(1, 9999):04d}"
    
    return f"{area}{dd}{mm}{yy}{seq}"

def generate_npwp():
    """Generate realistic but fake NPWP"""
    # Format: XX.XXX.XXX.X-XXX.XXX
    part1 = f"{random.randint(10, 99)}"
    part2 = f"{random.randint(100, 999)}"
    part3 = f"{random.randint(100, 999)}"
    part4 = f"{random.randint(1, 9)}"
    part5 = f"{random.randint(100, 999)}"
    part6 = f"{random.randint(100, 999)}"
    
    return f"{part1}.{part2}.{part3}.{part4}-{part5}.{part6}"

def generate_pt_data(palm_companies, num_additional_companies=50):
    """Generate comprehensive PT company data"""
    
    kbli_codes = generate_kbli_codes()
    suspicious_names = generate_suspicious_company_names()
    indonesian_names = generate_indonesian_names(200)  # Pool of names for founders/directors
    
    companies = []
    
    # Process existing palm companies (70% of total)
    for i, company in enumerate(palm_companies[:80]):  # Limit to 80 companies
        
        # Determine if this should be suspicious (20% chance)
        is_suspicious = random.random() < 0.2
        
        # Modal structure
        if is_suspicious:
            modal_dasar = random.randint(1000000000, 5000000000)  # 1-5 billion
            modal_ditempatkan = random.randint(int(modal_dasar * 0.1), int(modal_dasar * 0.3))
            modal_disetor = random.randint(int(modal_ditempatkan * 0.1), int(modal_ditempatkan * 0.5))  # Low actual capital
        else:
            modal_dasar = random.randint(10000000000, 100000000000)  # 10-100 billion
            modal_ditempatkan = random.randint(int(modal_dasar * 0.25), int(modal_dasar * 0.8))
            modal_disetor = random.randint(int(modal_ditempatkan * 0.7), modal_ditempatkan)  # High actual capital
        
        nilai_nominal = random.choice([1000000, 5000000, 10000000])  # 1M, 5M, or 10M per share
        jumlah_saham = modal_ditempatkan // nilai_nominal
        
        # Ownership structure
        num_shareholders = random.randint(1, 4) if not is_suspicious else random.randint(2, 6)
        shareholders = []
        remaining_percentage = 100.0
        
        for j in range(num_shareholders):
            if j == num_shareholders - 1:
                percentage = remaining_percentage
            else:
                max_pct = min(80, remaining_percentage - (num_shareholders - j - 1))
                percentage = round(random.uniform(10, max_pct), 2)
                remaining_percentage -= percentage
            
            shareholder_name = random.choice(indonesian_names)
            shareholders.append({
                'nama': shareholder_name,
                'nik': generate_nik(),
                'npwp': generate_npwp(),
                'persentase': percentage
            })
        
        # Directors and commissioners
        direktur = random.choice(indonesian_names)
        komisaris = random.choice(indonesian_names)
        
        # Company age (suspicious companies tend to be newer)
        if is_suspicious:
            company_age_days = random.randint(30, 365 * 2)  # 1 month to 2 years
        else:
            company_age_days = random.randint(365 * 3, 365 * 20)  # 3 to 20 years
        
        akta_date = datetime.now() - timedelta(days=company_age_days)
        
        company_data = {
            'company_id': f"PT_{i+1:04d}",
            'nama_perseroan': company if company.startswith('PT') else f"PT {company}",
            'kbli': random.choice(kbli_codes[:6]),  # Palm-related KBLI for real companies
            'alamat_lengkap': fake.address(),
            'kode_pos': fake.postcode(),
            'maksud_tujuan': "Usaha perkebunan kelapa sawit dan pengolahan hasil",
            'modal_dasar': modal_dasar,
            'modal_ditempatkan': modal_ditempatkan,
            'modal_disetor': modal_disetor,
            'nilai_nominal_saham': nilai_nominal,
            'jumlah_saham': jumlah_saham,
            'pemegang_saham': shareholders,
            'direktur_utama': direktur,
            'direktur_nik': generate_nik(),
            'direktur_npwp': generate_npwp(),
            'komisaris_utama': komisaris,
            'komisaris_nik': generate_nik(),
            'komisaris_npwp': generate_npwp(),
            'jangka_waktu': "Tidak terbatas" if not is_suspicious else f"{random.randint(10, 25)} tahun",
            'tanggal_akta': akta_date.strftime('%Y-%m-%d'),
            'notaris': fake.name(),
            'npwp_perusahaan': generate_npwp(),
            'status_perusahaan': 'Aktif',
            'is_suspicious': is_suspicious,
            'risk_score': random.randint(70, 95) if is_suspicious else random.randint(10, 40)
        }
        
        companies.append(company_data)
    
    # Add pure shell/front companies (30% of total)
    for i in range(num_additional_companies):
        company_name = random.choice(suspicious_names)
        
        # Shell companies characteristics
        modal_dasar = random.randint(500000000, 2000000000)  # Low capital
        modal_ditempatkan = random.randint(int(modal_dasar * 0.25), int(modal_dasar * 0.5))
        modal_disetor = random.randint(int(modal_ditempatkan * 0.1), int(modal_ditempatkan * 0.3))  # Very low actual capital
        
        nilai_nominal = 1000000  # Standard 1M per share
        jumlah_saham = modal_ditempatkan // nilai_nominal
        
        # Complex ownership (typical for shells)
        num_shareholders = random.randint(3, 8)
        shareholders = []
        remaining_percentage = 100.0
        
        for j in range(num_shareholders):
            if j == num_shareholders - 1:
                percentage = remaining_percentage
            else:
                percentage = round(random.uniform(5, 30), 2)
                remaining_percentage -= percentage
            
            shareholder_name = random.choice(indonesian_names)
            shareholders.append({
                'nama': shareholder_name,
                'nik': generate_nik(),
                'npwp': generate_npwp(),
                'persentase': percentage
            })
        
        # Recent incorporation
        company_age_days = random.randint(7, 180)  # 1 week to 6 months
        akta_date = datetime.now() - timedelta(days=company_age_days)
        
        company_data = {
            'company_id': f"SH_{i+1:04d}",
            'nama_perseroan': company_name,
            'kbli': random.choice(kbli_codes[6:]),  # Unrelated KBLI for shells
            'alamat_lengkap': fake.address(),
            'kode_pos': fake.postcode(),
            'maksud_tujuan': "Perdagangan umum dan jasa konsultan",
            'modal_dasar': modal_dasar,
            'modal_ditempatkan': modal_ditempatkan,
            'modal_disetor': modal_disetor,
            'nilai_nominal_saham': nilai_nominal,
            'jumlah_saham': jumlah_saham,
            'pemegang_saham': shareholders,
            'direktur_utama': random.choice(indonesian_names),
            'direktur_nik': generate_nik(),
            'direktur_npwp': generate_npwp(),
            'komisaris_utama': random.choice(indonesian_names),
            'komisaris_nik': generate_nik(),
            'komisaris_npwp': generate_npwp(),
            'jangka_waktu': f"{random.randint(5, 15)} tahun",
            'tanggal_akta': akta_date.strftime('%Y-%m-%d'),
            'notaris': fake.name(),
            'npwp_perusahaan': generate_npwp(),
            'status_perusahaan': 'Aktif',
            'is_suspicious': True,
            'risk_score': random.randint(80, 98)
        }
        
        companies.append(company_data)
    
    return companies

def save_to_multiple_formats(companies, base_filename='pt_data'):
    """Save data in multiple formats for different use cases"""
    
    # Flatten data for CSV export
    flattened_data = []
    for company in companies:
        base_data = {k: v for k, v in company.items() if k != 'pemegang_saham'}
        
        # Add shareholder info (take first 3 shareholders to avoid too many columns)
        for i, shareholder in enumerate(company['pemegang_saham'][:3]):
            base_data[f'pemegang_saham_{i+1}_nama'] = shareholder['nama']
            base_data[f'pemegang_saham_{i+1}_nik'] = shareholder['nik']
            base_data[f'pemegang_saham_{i+1}_npwp'] = shareholder['npwp']
            base_data[f'pemegang_saham_{i+1}_persentase'] = shareholder['persentase']
        
        flattened_data.append(base_data)
    
    # Save as CSV
    df = pd.DataFrame(flattened_data)
    df.to_csv(f'{base_filename}.csv', index=False)
    
    # Save detailed JSON for complex relationships
    import json
    with open(f'{base_filename}_detailed.json', 'w', encoding='utf-8') as f:
        json.dump(companies, f, ensure_ascii=False, indent=2, default=str)
    
    # Create separate shareholders table for relational database
    shareholders_data = []
    for company in companies:
        for shareholder in company['pemegang_saham']:
            shareholders_data.append({
                'company_id': company['company_id'],
                'nama_pemegang_saham': shareholder['nama'],
                'nik': shareholder['nik'],
                'npwp': shareholder['npwp'],
                'persentase_kepemilikan': shareholder['persentase']
            })
    
    shareholders_df = pd.DataFrame(shareholders_data)
    shareholders_df.to_csv(f'{base_filename}_shareholders.csv', index=False)
    
    print(f"Generated {len(companies)} companies:")
    print(f"- Legitimate companies: {len([c for c in companies if not c['is_suspicious']])}")
    print(f"- Suspicious companies: {len([c for c in companies if c['is_suspicious']])}")
    print(f"Files saved: {base_filename}.csv, {base_filename}_detailed.json, {base_filename}_shareholders.csv")

# Example usage
if __name__ == "__main__":
    # Load your palm oil companies
    palm_companies = load_palm_companies('123.csv')
    
    # Generate synthetic PT data
    companies = generate_pt_data(palm_companies, num_additional_companies=30)
    
    # Save in multiple formats
    save_to_multiple_formats(companies, 'jalak_hijau_pt_data')
    
    # Display sample suspicious patterns
    suspicious_companies = [c for c in companies if c['is_suspicious']]
    print(f"\nSample suspicious patterns detected:")
    for company in suspicious_companies[:3]:
        capital_ratio = (company['modal_disetor'] / company['modal_ditempatkan']) * 100
        print(f"- {company['nama_perseroan']}: Capital paid-in only {capital_ratio:.1f}% of placed capital")
        print(f"  Age: {(datetime.now() - datetime.strptime(company['tanggal_akta'], '%Y-%m-%d')).days} days")
        print(f"  Risk Score: {company['risk_score']}")
        print()