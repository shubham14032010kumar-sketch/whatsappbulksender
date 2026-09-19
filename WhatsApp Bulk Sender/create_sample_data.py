import csv

data = [
    ["Name", "Phone", "City", "OfferCode"],
    ["Rahul Sharma", "+919876543210", "Mumbai", "FESTIVE50"],
    ["Priya Patel", "+919812345678", "Ahmedabad", "WELCOME100"],
    ["Amit Kumar", "919988776655", "Delhi", "SPECIAL20"]
]

with open("sample_contacts.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(data)

print("Created sample_contacts.csv successfully.")
