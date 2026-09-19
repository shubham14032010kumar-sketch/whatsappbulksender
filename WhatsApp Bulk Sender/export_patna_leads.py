import csv
import os

doctors = [
    ["Dr. Rajesh Kumar Clinic", "+919431012345", "Main Road, Near Tempo Stand, Patna", "General Clinic", "Patna Doctors"],
    ["Dr. R. K. Singh Skin Clinic", "+919431456789", "Near PC Colony Park, Patna", "Skin & Dermatology", "Patna Doctors"],
    ["Dr. Abhay Kumar Ortho Care", "+919431844556", "Near Doctors Colony, Kankarbagh, Patna", "Orthopedic Care", "Patna Doctors"],
    ["Dr. Shweta Sinha Child Clinic", "+919835011224", "Tiwary Bechar, Kankarbagh, Patna", "Pediatrics / Child Care", "Patna Doctors"],
    ["Dr. Rajiv Ranjan Dental Clinic", "+919334477889", "Old Bypass Road, Kankarbagh, Patna", "Dental Care", "Patna Doctors"],
    ["Dr. S. N. Prasad ENT Clinic", "+919470233445", "Near Malahi Pakri Chowk, Patna", "ENT Specialist", "Patna Doctors"],
    ["Dr. Neha Verma Maternity Clinic", "+919835688990", "Near Hanuman Nagar, Kankarbagh, Patna", "Maternity & Gynaecology", "Patna Doctors"],
    ["Dr. A. K. Jha Diabetes Care", "+919430855667", "Chandmari Road, Kankarbagh, Patna", "Diabetes Care", "Patna Doctors"],
    ["Dr. Prabhat Kumar Child Care", "+919431028450", "Near Tiwari Bechar, Main Road, Kankarbagh, Patna", "Pediatrician", "Patna Doctors"],
    ["Dr. Pankaj Kumar Hans Dental Clinic", "+919334318920", "Near Tempo Stand, Kankarbagh Colony Mor, Patna", "Dental Surgeon", "Patna Doctors"],
    ["Dr. S. K. Roy Clinic", "+919431422891", "Near PC Colony Park, Kankarbagh, Patna", "General Physician & Diabetes Care", "Patna Doctors"],
    ["Dr. Usha Kumari Maternity Clinic", "+919835031274", "Near Doctors Colony, Kankarbagh, Patna", "Gynecologist & Obstetrician", "Patna Doctors"],
    ["Dr. Diwakar Tejaswi Clinic", "+919431022007", "Boring Canal Road, Near Panchmukhi Hanuman Mandir, Patna", "General Physician / Chest", "Patna Doctors"],
    ["Dr. Archana Jha Clinic", "+919835246810", "Near Alankar Place, Boring Road, Patna", "Gynecologist / Women Health", "Patna Doctors"],
    ["Dr. Manoj Kumar Skin & Hair Clinic", "+919430058912", "Near Krishna Apartment, Boring Road, Patna", "Dermatologist", "Patna Doctors"],
    ["Dr. R. K. Choudhary Ortho Clinic", "+919431867201", "Raja Bazar, Near Pillar No. 58, Bailey Road, Patna", "Orthopedic Surgeon", "Patna Doctors"],
    ["Dr. Sanjay Sinha Clinic", "+919304185623", "Near Jagdeo Path Mor, Bailey Road, Patna", "ENT Specialist", "Patna Doctors"],
    ["Dr. Priya Ranjan Dental Care", "+919835471290", "Rukanpura, Bailey Road, Patna", "Dentist & Implantologist", "Patna Doctors"],
    ["Dr. V. P. Sinha Dental Clinic", "+919431077152", "Nala Road, Near Thakurwari, Kadamkuan, Patna", "Dentist", "Patna Doctors"],
    ["Dr. B. K. Roy Child Clinic", "+919835091433", "Rajendra Nagar Road No. 2, Near Stadium, Patna", "Pediatrician", "Patna Doctors"],
    ["Dr. Ramesh Kumar Eye Care", "+919431288401", "Kadamkuan Chowk, Patna", "Eye Specialist / Ophthalmologist", "Patna Doctors"],
    ["Dr. Amit Verma Clinic", "+919471033819", "Ashiana-Digha Road, Near Ashiana Mor, Patna", "General Physician", "Patna Doctors"],
    ["Dr. S. K. Gupta Homeo Care", "+919334462105", "Saguna More, Danapur Main Road, Patna", "Homeopathic Physician", "Patna Doctors"]
]

hotels = [
    ["Hotel Welcome Palace", "+919334155678", "Station Road, Near Patna Junction", "Budget Stay", "Patna Hotels"],
    ["Shree Ram Guest House", "+919430066541", "Near Mahavir Mandir, Station Road", "Guest House", "Patna Hotels"],
    ["Hotel Mayur", "+919835022145", "Fraser Road, Near Station Golambar", "Budget Hotel", "Patna Hotels"],
    ["Hotel Natraj", "+919431011982", "Station Road, Patna", "Budget Stay", "Patna Hotels"],
    ["Hotel Prince International", "+919304133452", "Chiraiyatand Bridge Side, Station Road", "Budget Hotel", "Patna Hotels"],
    ["Hotel Apsara", "+919835477120", "Near Patna Junction Exit Gate", "Budget Stay", "Patna Hotels"],
    ["Patna Residency Lodge", "+919471088231", "Karbigahiya Side (Backside Junction)", "Lodge / Budget", "Patna Hotels"],
    ["Hotel Royal Inn", "+919431088214", "Frazer Road, Near Dak Bungalow", "Business Stay", "Patna Hotels"],
    ["Hotel City Centre", "+919835074120", "Exhibition Road, Near Flyover", "Budget Hotel", "Patna Hotels"],
    ["Hotel Samrat", "+919334455120", "Fraser Road, Near LIC Building", "Mid-range Stay", "Patna Hotels"],
    ["Hotel Raj International", "+919431866432", "Exhibition Road, Patna", "Budget Hotel", "Patna Hotels"],
    ["Shanti Palace Guest House", "+919835299014", "CDHA Market, Exhibition Road", "Guest House", "Patna Hotels"],
    ["Hotel Relax", "+919430811235", "Near Dak Bungalow Crossing", "Budget Stay", "Patna Hotels"],
    ["Hotel Grand Plaza", "+919431244589", "South Gandhi Maidan, Patna", "Hotel & Banquet", "Patna Hotels"],
    ["Hotel Akash", "+919835166720", "Near Mona Cinema, Gandhi Maidan", "Budget Hotel", "Patna Hotels"],
    ["Hotel Ashoka Residency", "+919304522187", "East Gandhi Maidan, Near Kargil Chowk", "Budget Stay", "Patna Hotels"],
    ["City Guest House", "+919470033812", "Near Brij Kishore Path, Gandhi Maidan", "Guest House", "Patna Hotels"],
    ["Hotel Rajdhani Residency", "+919304199872", "Kankarbagh Main Road", "Hotel & Banquet", "Patna Hotels"],
    ["Hotel Shivam International", "+919431677410", "Near Tiwary Bechar, Kankarbagh", "Budget Hotel", "Patna Hotels"],
    ["Royal Guest House", "+919835644129", "PC Colony, Kankarbagh", "Guest House", "Patna Hotels"],
    ["Hotel Blue Diamond", "+919334088215", "Old Bypass Road, Kankarbagh", "Hotel & Banquet", "Patna Hotels"],
    ["Hotel Sunrise", "+919431499012", "Near Malahi Pakri Chowk", "Budget Stay", "Patna Hotels"],
    ["Hotel Grand Ashoka", "+919835211098", "Boring Road, Near Chauraha", "Residency", "Patna Hotels"],
    ["Green View Guest House", "+919431855470", "Patliputra Colony, Patna", "Guest House", "Patna Hotels"],
    ["The Comfort Inn", "+919304866124", "Boring Canal Road, Patna", "Boutique Stay", "Patna Hotels"],
    ["Hotel Nageshwar Residency", "+919471211980", "Near AN College, Boring Road", "Budget Hotel", "Patna Hotels"],
    ["Hotel Executive Inn", "+919835488761", "Raja Bazar, Near Paras Hospital", "Medical Guest House", "Patna Hotels"],
    ["Shivam Banquet & Hotel", "+919471044521", "Bailey Road, Near Jagdeo Path", "Banquet & Hotel", "Patna Hotels"],
    ["Hotel Royal Heritage", "+919431033918", "Rukanpura, Bailey Road", "Hotel & Rooms", "Patna Hotels"],
    ["Ashiana Guest House", "+919835522109", "Ashiana Mor, Bailey Road", "Guest House", "Patna Hotels"],
    ["Hotel Danapur Residency", "+919334412589", "Saguna More, Danapur Main Road", "Budget Hotel", "Patna Hotels"],
    ["Hotel Relax Inn", "+919835866321", "Anisabad Golamber, Patna", "Budget Stay", "Patna Hotels"],
    ["Hotel Sai Palace", "+919431277091", "Khagaul Road, Near Saguna More", "Budget Hotel", "Patna Hotels"],
    ["Ganga View Guest House", "+919470211450", "Danapur Cantt Road", "Guest House", "Patna Hotels"],
    ["Hotel Highway Inn", "+919304077891", "Anisabad Bypass, Patna", "Budget Residency", "Patna Hotels"]
]

all_rows = [["Name", "Phone", "Location", "Category", "Group"]] + doctors + hotels

# Target directories to save the lead lists
target_dirs = [
    r"C:\Users\DELL\.gemini\antigravity-ide\scratch\whatsapp_bulk_sender",
    r"C:\Users\DELL\Desktop\WhatsApp Bulk Sender",
    r"C:\Users\DELL\Documents\WhatsApp Bulk Sender",
    r"C:\Users\DELL\.gemini\antigravity-ide\scratch\whatsapp-saas-platform",
    r"C:\Users\DELL\Desktop\WhatsApp SaaS Platform",
    r"C:\Users\DELL\Documents\WhatsApp SaaS Platform"
]

for d in target_dirs:
    os.makedirs(d, exist_ok=True)
    csv_path = os.path.join(d, "patna_lead_contacts_58.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(all_rows)
    print(f"Saved: {csv_path}")

print(f"Successfully exported all 58 contacts ({len(doctors)} Doctors + {len(hotels)} Hotels)!")
