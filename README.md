# 🧾 Invoice Analytics API

A simple Django REST API for managing invoices and performing currency-based analytics using MongoDB and real-time exchange rates. Built with **MongoEngine**, powered by **Docker**, and tested with 💯% confidence!

---

## 🚀 Features

- 📥 **Create** invoices with automatic USD conversion  
- 📄 **Read** single or all invoices  
- ✏️ **Update** or 🗑️ **Delete** invoices  
- 💱 **Fetch exchange rates** for any invoice  
- 📊 **Total revenue** analytics in any currency  
- 📉 **Average invoice** value with conversion  
- 🧪 Unit tests & Postman collection for testing  

---

## 🛠️ Tech Stack

| Tech        | Usage                          |
|-------------|--------------------------------|
| Django      | Web framework                  |
| Django REST | API framework                  |
| MongoDB     | Document database (Dockerized) |
| MongoEngine | ODM (Object-Document Mapper)   |
| Docker      | MongoDB container              |
| Python      | Main programming language      |
| Postman     | API testing (collection file)  |

---

## 🧰 Getting Started

### 📦 1. Clone & Install Dependencies

```bash
git clone https://github.com/yourusername/invoice-analytics-api.git
cd invoice-analytics-api
pip install -r requirements.txt
```

### 2. Run MongoDB with Docker
```bash
docker run -d -p 27017:27017 --name mongo-invoice mongo
```
### 3. Run the Django Server
```bash
python manage.py runserver
```

🧪 Running Tests
```bash
python manage.py test
```
✅ Tests cover:

- GET/POST/PUT/DELETE endpoints
- Exchange rate & currency validation
- Analytics: total revenue and average invoice
- Error scenarios (404, invalid currency, etc.)

📬 API Collection (Postman)

You can test all endpoints using the provided Postman collection:

👉 Import postman_collection.json into Postman

🧪 Covers all request types and use-cases

📌 Notes
- MongoDB is expected to run on localhost:27017 via Docker
- Uses MongoEngine instead of Django's ORM
- Make sure requirements.txt is installed before running
- Ensure settings.py is configured with the correct MongoDB URI
- Test database is auto-configured when running tests

