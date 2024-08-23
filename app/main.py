import logging
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer
from . import models, schemas, crud, database
import csv
from io import StringIO
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = [
    "http://localhost:4200",  
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Map party codes to full names
PARTY_CODE_MAP = {
    "C": "Conservative Party",
    "L": "Labour Party",
    "UKIP": "UKIP",
    "LD": "Liberal Democrats",
    "G": "Green Party",
    "Ind": "Independent",
    "SNP": "SNP"
}

# Log configuration
logging.basicConfig(filename='election-result-backend.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(database.get_db)):

    """
    Uploads a CSV file and processes its election result data.

    Args:
        file (UploadFile): The CSV file to upload.
        db (Session): The database session.

    Returns:
        JSONResponse: A JSON response indicating success or failure.

    Raises:
        HTTPException: If the uploaded file is not a CSV or if an error occurs during processing.
    """

    logging.info('Acessing upload_csv method.!')
    if not file.filename.endswith('.csv'):
        logging.info('Uploaded wrong file, File must be a CSV.')
        raise HTTPException(status_code=400, detail="File must be a CSV.")

    contents = await file.read()

    # Handle escaped \, in constituency names
    csv_content = contents.decode("utf-8").replace('\\,', '')
    csv_data = StringIO(csv_content)
    reader = csv.reader(csv_data)
    #reader = csv.reader(csv_data, escapechar='\,')

    for row in reader:  
        constituency = row[0]
        
        total_votes = sum(int(row[i]) for i in range(1, len(row), 2))
        
        # Iterate over party code and votes pairs
        for i in range(1, len(row), 2):
            votes = int(row[i])
            party_code = row[i + 1].strip()

            party_name = PARTY_CODE_MAP.get(party_code)
            if not party_name:
                continue

            percentage = (votes / total_votes) * 100

            # Check if a record already exists for the same constituency and party
            existing_result = crud.get_constituency_result(db, constituency, party_name)

            if existing_result:
                # If it exists, update the existing record
                existing_result.votes = votes
                existing_result.percentage = percentage
                db.commit()
                db.refresh(existing_result)
            else:
                # If it doesn't exist, create a new record
                result = schemas.ConstituencyCreate(
                    constituency=constituency,
                    party=party_name,
                    votes=votes,
                    percentage=percentage
                )
                crud.create_result(db=db, result=result)
    logging.info('Data saved sucessfully.!')
    return HTTPException(status_code=200, detail="Data saved sucessfully !")


@app.get("/results")
def get_total_results(db: Session = Depends(database.get_db)):

    """
    Retrieve the total number of results from the database.

    This endpoint is used to get the total number of results stored in the database.
    It uses the `get_total_results` function from the `crud` module to fetch the data.

    Args:
        db (Session): The database session object, provided by FastAPI's Depends function.

    Returns:
        The total number of results stored in the database.
    """
    logging.info("Acessing get_total_results method.")
    results = crud.get_total_results(db)
    if not results:
        logging.info("No results found.")
        raise HTTPException(status_code=404, detail="No results found")
    return results


@app.get("/constituencies")
def get_constituencies(db: Session = Depends(database.get_db)):

    """
    Retrieves a list of all constituencies from the database.

    Args:
        db (Session): A database session object.

    Returns:
        list: A list of constituency objects.

    Raises:
        HTTPException: If no constituencies are found in the database.
    """
    logging.info("Acessing get_constituencies method.")
    results = crud.get_constituencies(db)
    logging.info(f'results : "{results}')
    if not results:
        logging.info("No results found.")
        raise HTTPException(status_code=404, detail="No results found")
    return results