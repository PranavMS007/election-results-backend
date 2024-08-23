from sqlalchemy import func,cast, Integer
from sqlalchemy.orm import Session
from . import models, schemas


def get_constituency_result(db: Session, constituency: str, party: str):
    """
    Retrieve the election result for a specific constituency and party from the database.

    This function queries the database for the election results associated with the given
    constituency and party. It returns the first matching result found.

    Parameters:
    db (Session): The SQLAlchemy session object used to interact with the database.
    constituency (str): The name of the constituency for which to retrieve the election result.
    party (str): The name of the political party for which to retrieve the election result.

    Returns:
    models.ConstituencyResult or None: The first matching ConstituencyResult object if found,
    otherwise None if no result matches the provided constituency and party.
    """
    # Query the database for the ConstituencyResult
    return db.query(models.ConstituencyResult).filter_by(constituency=constituency, party=party).first()

def create_result(db: Session, result: schemas.ConstituencyCreate):
    """
    Create a new constituency result in the database.

    Args:
        db (Session): The SQLAlchemy database session.
        result (schemas.ConstituencyCreate): The constituency result data to be created.

    Returns:
        models.ConstituencyResult: The created constituency result.
    """
     # Create a new ConstituencyResult object with the provided data
    db_result = models.ConstituencyResult(
        constituency=result.constituency,
        party=result.party,
        votes=result.votes,
        percentage=result.percentage
    )
    # Add the new result to the database session
    db.add(db_result)
     # Commit the changes to the database
    db.commit()
    # Refresh the database object to ensure it has the latest data
    db.refresh(db_result)
    # Return the created constituency result
    return db_result


def get_total_results(db: Session):
    """
    Retrieves the total number of votes and total number of MPs per party.

    Args:
        db (Session): The database session object.

    Returns:
        dict: A dictionary containing the total votes and total MPs for each party.
    """
   # Subquery to determine the winning party in each constituency
    subquery = (
        db.query(
            models.ConstituencyResult.constituency,
            models.ConstituencyResult.party,
            func.rank().over(
                partition_by=models.ConstituencyResult.constituency,
                order_by=cast(models.ConstituencyResult.votes, Integer).desc()
            ).label("rank")
        )
        .subquery()
    )

    # Query to get the total MPs per party
    total_mps_query = (
        db.query(
            subquery.c.party,
            func.count().label("total_mps")
        )
        .filter(subquery.c.rank == 1)  # Only consider the top-ranked party in each constituency
        .group_by(subquery.c.party)
        .all()
    )

    # Query to get total votes per party
    total_votes_query = (
        db.query(
            models.ConstituencyResult.party,
            func.sum(cast(models.ConstituencyResult.votes, Integer)).label("total_votes")
        )
        .group_by(models.ConstituencyResult.party)
        .all()
    )

    # Combine results into a single response
    result = {party: {"total_votes": 0, "total_mps": 0} for party, _ in total_votes_query}
    for party, total_votes in total_votes_query:
        result[party]["total_votes"] = total_votes

    for party, total_mps in total_mps_query:
        if party in result:
            result[party]["total_mps"] = total_mps

    return result


def get_constituencies(db: Session):
    """
    Retrieve the results of elections for constituencies, including total votes and percentages
    per party, as well as the winning party for each constituency.

    Args:
        db (Session): The database session used to query the election results.

    Returns:
        List[Dict]: A list of dictionaries where each dictionary contains:
            - constituency_name (str): The name of the constituency.
            - results (List[Dict]): A list of results for each party in the constituency,
              where each result contains:
                - party (str): The name of the party.
                - votes (int): The total number of votes received by the party.
                - percentage (float): The percentage of total votes received by the party.
            - winning_party (str): The name of the party that received the most votes in the constituency.
    """
    # Query to get total votes and percentages per party per constituency
    subquery = (
        db.query(
            models.ConstituencyResult.constituency.label('constituency_name'),
            models.ConstituencyResult.party,
            func.sum(cast(models.ConstituencyResult.votes, Integer)).label('total_votes'),
            (func.sum(cast(models.ConstituencyResult.votes, Integer)) * 100 /
             func.sum(func.sum(cast(models.ConstituencyResult.votes, Integer))).over(
                 partition_by=models.ConstituencyResult.constituency)).label('percentage')
        )
        .group_by(models.ConstituencyResult.constituency, models.ConstituencyResult.party)
        .subquery()
    )

    # Query to get the winning party per constituency
    main_query = (
        db.query(
            subquery.c.constituency_name,
            subquery.c.party,
            subquery.c.total_votes,
            subquery.c.percentage,
            func.max(subquery.c.total_votes).over(partition_by=subquery.c.constituency_name).label('max_votes')
        )
        .order_by(subquery.c.constituency_name)
    ).all()

    # Process the results into the required structure
    results_dict = {}
    for result in main_query:
        constituency_name = result.constituency_name

        if constituency_name not in results_dict:
            results_dict[constituency_name] = {
                "constituency_name": constituency_name,
                "results": [],
                "winning_party": None
            }

        results_dict[constituency_name]["results"].append({
            "party": result.party,
            "votes": result.total_votes,
            "percentage": round(result.percentage, 2)
        })

        # Determine the winning party
        if result.total_votes == result.max_votes:
            results_dict[constituency_name]["winning_party"] = result.party

    # Convert results_dict to a list
    final_results = list(results_dict.values())

    return final_results