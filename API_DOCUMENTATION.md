# Excel File Management API Documentation

Complete REST API for managing Excel (.xlsx) files in the Fox Hardware Inventory system.

## Base URL
```
http://localhost:8000/api/files
```

## Authentication
Currently, the API does not require authentication for MVP. In production, add API key or session-based authentication.

---

## Endpoints

### 1. Upload File
**POST** `/api/files/upload`

Upload a new Excel file to the system.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field containing the Excel file

**Response:**
```json
{
  "success": true,
  "file": {
    "filename": "inventory.xlsx",
    "path": "uploads/inventory.xlsx",
    "size": 12345,
    "uploaded_at": "2025-01-29T12:00:00",
    "columns": ["Computer Name", "Department", "Operating System"],
    "row_count": 98,
    "auto_mapping": {
      "asset_tag": "Computer Name",
      "department": "Department",
      "operating_system": "Operating System"
    },
    "sample_data": [...]
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/files/upload \
  -F "file=@inventory.xlsx"
```

---

### 2. List Files
**GET** `/api/files/list`

List all uploaded files and import history.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 50, max: 100)

**Response:**
```json
{
  "files": [
    {
      "filename": "inventory.xlsx",
      "path": "uploads/inventory.xlsx",
      "size": 12345,
      "created_at": "2025-01-29T12:00:00",
      "modified_at": "2025-01-29T12:00:00"
    }
  ],
  "imports": [
    {
      "id": 1,
      "filename": "inventory.xlsx",
      "uploaded_at": "2025-01-29T12:00:00",
      "status": "completed",
      "records_processed": 98,
      "records_created": 95,
      "records_updated": 3,
      "records_failed": 0
    }
  ],
  "total_files": 1,
  "total_imports": 1
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/files/list?skip=0&limit=50
```

---

### 3. Download File
**GET** `/api/files/download/{filename}`

Download an uploaded Excel file.

**Path Parameters:**
- `filename`: Name of the file to download

**Response:**
- File download (Excel file)

**cURL Example:**
```bash
curl -O http://localhost:8000/api/files/download/inventory.xlsx
```

---

### 4. Get File Info
**GET** `/api/files/{filename}/info`

Get detailed information about a specific file.

**Path Parameters:**
- `filename`: Name of the file

**Response:**
```json
{
  "filename": "inventory.xlsx",
  "path": "uploads/inventory.xlsx",
  "size": 12345,
  "created_at": "2025-01-29T12:00:00",
  "modified_at": "2025-01-29T12:00:00",
  "columns": ["Computer Name", "Department", "Operating System"],
  "row_count": 98,
  "auto_mapping": {...},
  "sample_data": [...],
  "import_status": {
    "imported": true,
    "import_id": 1,
    "import_status": "completed",
    "imported_at": "2025-01-29T12:00:00"
  }
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/files/inventory.xlsx/info
```

---

### 5. Delete File
**DELETE** `/api/files/{filename}`

Delete an uploaded file.

**Path Parameters:**
- `filename`: Name of the file to delete

**Response:**
```json
{
  "success": true,
  "message": "File inventory.xlsx deleted successfully"
}
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/files/inventory.xlsx
```

---

### 6. Get File Columns
**GET** `/api/files/{filename}/columns`

Get column information from an Excel file.

**Path Parameters:**
- `filename`: Name of the file

**Response:**
```json
{
  "filename": "inventory.xlsx",
  "columns": ["Computer Name", "Department", "Operating System"],
  "column_count": 3,
  "row_count": 98,
  "sample_data": [...]
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/files/inventory.xlsx/columns
```

---

### 7. Parse File
**POST** `/api/files/{filename}/parse`

Parse an Excel file with optional column mapping and return transformed data.

**Path Parameters:**
- `filename`: Name of the file

**Query Parameters:**
- `mapping` (optional): JSON string of column mapping
  ```json
  {
    "asset_tag": "Computer Name",
    "department": "Department",
    "operating_system": "Operating System"
  }
  ```

**Response:**
```json
{
  "filename": "inventory.xlsx",
  "total_rows": 98,
  "transformed_data": [
    {
      "asset_tag": "WJBKPWLT0RDJ",
      "department": "IT",
      "operating_system": "Windows 11",
      ...
    }
  ],
  "mapping_used": {...}
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/files/inventory.xlsx/parse?mapping=%7B%22asset_tag%22%3A%22Computer%20Name%22%7D"
```

---

### 8. Export File Data
**GET** `/api/files/{filename}/export`

Export file data in JSON or CSV format.

**Path Parameters:**
- `filename`: Name of the file

**Query Parameters:**
- `format` (optional): Export format - `json` or `csv` (default: `json`)

**Response:**
- JSON: Returns JSON object with data
- CSV: Returns CSV file download

**cURL Examples:**
```bash
# Export as JSON
curl http://localhost:8000/api/files/inventory.xlsx/export?format=json

# Export as CSV
curl -O http://localhost:8000/api/files/inventory.xlsx/export?format=csv
```

---

## Error Responses

All endpoints may return the following error responses:

**400 Bad Request:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

**404 Not Found:**
```json
{
  "detail": "File not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error message"
}
```

---

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/files"

# Upload a file
with open("inventory.xlsx", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/upload",
        files={"file": f}
    )
    print(response.json())

# List all files
response = requests.get(f"{BASE_URL}/list")
print(response.json())

# Get file info
response = requests.get(f"{BASE_URL}/inventory.xlsx/info")
print(response.json())

# Parse file with mapping
mapping = {
    "asset_tag": "Computer Name",
    "department": "Department"
}
response = requests.post(
    f"{BASE_URL}/inventory.xlsx/parse",
    params={"mapping": json.dumps(mapping)}
)
print(response.json())

# Download file
response = requests.get(f"{BASE_URL}/download/inventory.xlsx")
with open("downloaded.xlsx", "wb") as f:
    f.write(response.content)

# Delete file
response = requests.delete(f"{BASE_URL}/inventory.xlsx")
print(response.json())
```

---

## JavaScript/Fetch Example

```javascript
const BASE_URL = 'http://localhost:8000/api/files';

// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch(`${BASE_URL}/upload`, {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));

// List files
fetch(`${BASE_URL}/list`)
.then(res => res.json())
.then(data => console.log(data));

// Get file info
fetch(`${BASE_URL}/inventory.xlsx/info`)
.then(res => res.json())
.then(data => console.log(data));
```

---

## Security Notes

1. **Path Traversal Protection**: All filename parameters are validated to prevent directory traversal attacks
2. **File Size Limits**: Files are validated against `MAX_UPLOAD_SIZE` setting
3. **File Type Validation**: Only `.xlsx` and `.xls` files are accepted
4. **Production Recommendations**:
   - Add authentication/authorization
   - Implement rate limiting
   - Add file scanning for malware
   - Use secure file storage (S3, etc.)
   - Implement proper session management

---

## API Testing

You can test the API using:
- **cURL** (examples provided above)
- **Postman** or **Insomnia**
- **Python requests** library
- **JavaScript fetch** API
- **FastAPI automatic docs**: Visit `http://localhost:8000/docs` for interactive API documentation
