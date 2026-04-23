import pytest
import os
import json
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("API_KEY", "test_key")

    import core.db
    import app

    with open("tests/data/players_snapshot.json") as f:
        players_data = json.load(f)

    class MockCollection:
        def find(self, _):
            return players_data

    monkeypatch.setattr(core.db, "get_players_collection", lambda: MockCollection())

    app.app.config["TESTING"] = True

    with app.app.test_client() as client:
        yield client
      
# Test 1 (Before Draft)
data1 = {
  "relevant_stats": [],
  "budget": 182,
  "players_left_to_draft": 16,
  "unavailable_players": ["D. Baldwin", "F. Alvarez", "H. Goodman", "G. Moreno", "S. Horwitz", "R. Mauricio", "M. Muncy", "X. Edwards", "C.J. Abrams", "B. Turang", "T. Turner", "N. Hoerner", "F. Lindor", "G. Perdomo", "A. Burleson", "J. Merrill", "M. Harris", "C. Carroll", "P. Crow-Armstrong", "J. Walker", "B. Marsh", "J. Wood", "J. Soto", "K. Tucker", "Joey Ortiz", "K. Schwarber", "S. Imanaga", "S. Alcantara", "M. Boyd", "M. Keller", "A. Abbott", "C. Horton", "M. King", "B. Woodruff", "F. Peralta", "B. Pfaadt", "S. Strider", "P. Skenes", "J. Misiorowski", "Y. Yamamoto", "N. Cortes", "R. Iglesias",  "C. Kelly", "A. Ramirez", "N. Arenado", "M. Busch", "Austin Riley", "P. Smith", "F. Freeman", "M. Machado", "M. Winn", "E. De La Cruz", "D. Swanson", "W. Adames", "S. Frelick", "R. Acuna", "J. Hoo Lee", "V. Scott II", "J. Chourio", "M. Yastrzemski", "S. Suzuki", "D. Crews", "R. Lopez", "N. Lodolo", "C. Cavalli", "G. Holmes", "M. McGreevy", "J. Luzardo", "L. Webb", "C. Sanchez", "C. Sale", "N. Pivetta", "J. Taillon", "R. Ray", "B. Singer", "S. Ohtani"],
  "players": []
}

def test_1(client):
    response = client.post(
        "/value",
        json=data1,
        headers={
            "X-API-KEY": os.environ.get("API_KEY")
        }
    )

    assert response.status_code == 200

    data = response.get_json()
    assert "results" in data
    print(data["results"][:10])
    
# Test 2 (After Drafting 10 Players)
data2 = {
  "relevant_stats": [],
  "budget": 182,
  "players_left_to_draft": 16,
  "unavailable_players": ["D. Baldwin", "F. Alvarez", "H. Goodman", "G. Moreno", "S. Horwitz", "R. Mauricio", "M. Muncy", "X. Edwards", "C.J. Abrams", "B. Turang", "T. Turner", "N. Hoerner", "F. Lindor", "G. Perdomo", "A. Burleson", "J. Merrill", "M. Harris", "C. Carroll", "P. Crow-Armstrong", "J. Walker", "B. Marsh", "J. Wood", "J. Soto", "K. Tucker", "Joey Ortiz", "K. Schwarber", "S. Imanaga", "S. Alcantara", "M. Boyd", "M. Keller", "A. Abbott", "C. Horton", "M. King", "B. Woodruff", "F. Peralta", "B. Pfaadt", "S. Strider", "P. Skenes", "J. Misiorowski", "Y. Yamamoto", "N. Cortes", "R. Iglesias",  "C. Kelly", "A. Ramirez", "N. Arenado", "M. Busch", "Austin Riley", "P. Smith", "F. Freeman", "M. Machado", "M. Winn", "E. De La Cruz", "D. Swanson", "W. Adames", "S. Frelick", "R. Acuna", "J. Hoo Lee", "V. Scott II", "J. Chourio", "M. Yastrzemski", "S. Suzuki", "D. Crews", "R. Lopez", "N. Lodolo", "C. Cavalli", "G. Holmes", "M. McGreevy", "J. Luzardo", "L. Webb", "C. Sanchez", "C. Sale", "N. Pivetta", "J. Taillon", "R. Ray", "B. Singer", "S. Ohtani", "William Contreras", "Daylen Lile", "Fernando Tatis", "Mookie Betts", "Ketel Marte", "Marcus Semien", "Bryce Harper", "Bo Bichette", "Ozzie Albies", "Eugenio Suarez"],
  "players": []
}

def test_2(client):
    response = client.post(
        "/value",
        json=data2,
        headers={
            "X-API-KEY": os.environ.get("API_KEY")
        }
    )

    assert response.status_code == 200

    data = response.get_json()
    assert "results" in data
    print(data["results"][:10])
    
# Test 3 (After Drafting 50 Players)
data3 = {
  "relevant_stats": [],
  "budget": 33,
  "players_left_to_draft": 7,
  "unavailable_players": ["D. Baldwin", "F. Alvarez", "H. Goodman", "G. Moreno", "S. Horwitz", "R. Mauricio", "M. Muncy", "X. Edwards", "C.J. Abrams", "B. Turang", "T. Turner", "N. Hoerner", "F. Lindor", "G. Perdomo", "A. Burleson", "J. Merrill", "M. Harris", "C. Carroll", "P. Crow-Armstrong", "J. Walker", "B. Marsh", "J. Wood", "J. Soto", "K. Tucker", "Joey Ortiz", "K. Schwarber", "S. Imanaga", "S. Alcantara", "M. Boyd", "M. Keller", "A. Abbott", "C. Horton", "M. King", "B. Woodruff", "F. Peralta", "B. Pfaadt", "S. Strider", "P. Skenes", "J. Misiorowski", "Y. Yamamoto", "N. Cortes", "R. Iglesias",  "C. Kelly", "A. Ramirez", "N. Arenado", "M. Busch", "Austin Riley", "P. Smith", "F. Freeman", "M. Machado", "M. Winn", "E. De La Cruz", "D. Swanson", "W. Adames", "S. Frelick", "R. Acuna", "J. Hoo Lee", "V. Scott II", "J. Chourio", "M. Yastrzemski", "S. Suzuki", "D. Crews", "R. Lopez", "N. Lodolo", "C. Cavalli", "G. Holmes", "M. McGreevy", "J. Luzardo", "L. Webb", "C. Sanchez", "C. Sale", "N. Pivetta", "J. Taillon", "R. Ray", "B. Singer", "S. Ohtani", "William Contreras", "Daylen Lile", "Fernando Tatis", "Mookie Betts", "Ketel Marte", "Marcus Semien", "Bryce Harper", "Bo Bichette", "Ozzie Albies", "Eugenio Suarez", "Austin Riley", "Miguel Rojas", "Alex Bregman", "Blake Snell", "Zac Gallen", "Mason Miller", "Otto Lopez", "Ezekiel Tovar", "Matt Chapman", "Alex Bohm", "Matt Olson", "Kyle Stowers", "Tyler Glasnow", "Will Smith", "Edwin Diaz", "Luis Garcia", "Eury Perez", "Luis Robert", "Brandon Lowe", "Devin Williams", "Ian Happ", "Aaron Nola", "TJ Friedl", "Jhoan Duran", "Xander Bogaerts", "Rafael Devers", "Merrill Kelly", "Jorge Polanco", "Mickey Moniak", "Zack Wheeler", "Emmet Sheehan", "Teoscar Hernandez", "Daniel Palencia", "Spencer Steer", "Brenton Doyle", "Bryson Stott", "Joe Musgrove", "Carlos Santana", "JT Realmuto", "Trevor Megill"],
  "players": []
}

def test_3(client):
    response = client.post(
        "/value",
        json=data3,
        headers={
            "X-API-KEY": os.environ.get("API_KEY")
        }
    )

    assert response.status_code == 200

    data = response.get_json()
    assert "results" in data
    print(data["results"][:10])
    
# Test 4 (After Drafting 100 Players)
data4 = {
  "relevant_stats": [],
  "budget": 1,
  "players_left_to_draft": 1,
  "unavailable_players": ["D. Baldwin", "F. Alvarez", "H. Goodman", "G. Moreno", "S. Horwitz", "R. Mauricio", "M. Muncy", "X. Edwards", "C.J. Abrams", "B. Turang", "T. Turner", "N. Hoerner", "F. Lindor", "G. Perdomo", "A. Burleson", "J. Merrill", "M. Harris", "C. Carroll", "P. Crow-Armstrong", "J. Walker", "B. Marsh", "J. Wood", "J. Soto", "K. Tucker", "Joey Ortiz", "K. Schwarber", "S. Imanaga", "S. Alcantara", "M. Boyd", "M. Keller", "A. Abbott", "C. Horton", "M. King", "B. Woodruff", "F. Peralta", "B. Pfaadt", "S. Strider", "P. Skenes", "J. Misiorowski", "Y. Yamamoto", "N. Cortes", "R. Iglesias",  "C. Kelly", "A. Ramirez", "N. Arenado", "M. Busch", "Austin Riley", "P. Smith", "F. Freeman", "M. Machado", "M. Winn", "E. De La Cruz", "D. Swanson", "W. Adames", "S. Frelick", "R. Acuna", "J. Hoo Lee", "V. Scott II", "J. Chourio", "M. Yastrzemski", "S. Suzuki", "D. Crews", "R. Lopez", "N. Lodolo", "C. Cavalli", "G. Holmes", "M. McGreevy", "J. Luzardo", "L. Webb", "C. Sanchez", "C. Sale", "N. Pivetta", "J. Taillon", "R. Ray", "B. Singer", "S. Ohtani", "William Contreras", "Daylen Lile", "Fernando Tatis", "Mookie Betts", "Ketel Marte", "Marcus Semien", "Bryce Harper", "Bo Bichette", "Ozzie Albies", "Eugenio Suarez", "Austin Riley", "Miguel Rojas", "Alex Bregman", "Blake Snell", "Zac Gallen", "Mason Miller", "Otto Lopez", "Ezekiel Tovar", "Matt Chapman", "Alex Bohm", "Matt Olson", "Kyle Stowers", "Tyler Glasnow", "Will Smith", "Edwin Diaz", "Luis Garcia", "Eury Perez", "Luis Robert", "Brandon Lowe", "Devin Williams", "Ian Happ", "Aaron Nola", "TJ Friedl", "Jhoan Duran", "Xander Bogaerts", "Rafael Devers", "Merrill Kelly", "Jorge Polanco", "Mickey Moniak", "Zack Wheeler", "Emmet Sheehan", "Teoscar Hernandez", "Daniel Palencia", "Spencer Steer", "Brenton Doyle", "Bryson Stott", "Joe Musgrove", "Carlos Santana", "JT Realmuto", "Trevor Megill", "Miguel Amaya", "Oneil Cruz", "Christian Yelich", "Luis Arraez", "Jakob Marsee", "Noelvi Marte", "Liam Hicks", "Hunter Greene", "Emilio Pagan", "Ryan O'Hearn", "Andy Pages", "Bryan Reynolds", "Freddy Fermin", "Matt McLain", "Ryan Walker", "Tyler Stephenson", "Tanner Scott", "Edward Cabrera", "Patrick Bailey", "Heliot Ramos", "Adolis Garcia", "Andrew Vaughn", "Tommy Edman", "Matt Svanson", "Pete Fairbanks", "Brett Baty", "Dennis Santana", "Tyler Freeman", "Ramon Laureano", "Jordan Beck", "Willy Castro", "Conor Norby", "Joey Wentz", "Kevin Ginkel", "Kodai Senga", "Tyler Mahle", "Abner Uribe", "Robert Suarez", "Ryne Nelson", "Nolan Gorman", "Kyle Karros", "Ben Brown", "Tobias Myers", "Quinn Priester", "Lourdes Gurriel", "Matt Shaw", "Gavin Sheets", "Jake Cronenworth", "Eduardo Rodriguez", "Luis Torrens"],
  "players": []
}

def test_4(client):
    response = client.post(
        "/value",
        json=data4,
        headers={
            "X-API-KEY": os.environ.get("API_KEY")
        }
    )

    assert response.status_code == 200

    data = response.get_json()
    assert "results" in data
    print(data["results"][:10])
    
# Test 5 (After Drafting 130 Players)
data5 = {
  "relevant_stats": [],
  "budget": 0,
  "players_left_to_draft": 0,
  "unavailable_players": ["D. Baldwin", "F. Alvarez", "H. Goodman", "G. Moreno", "S. Horwitz", "R. Mauricio", "M. Muncy", "X. Edwards", "C.J. Abrams", "B. Turang", "T. Turner", "N. Hoerner", "F. Lindor", "G. Perdomo", "A. Burleson", "J. Merrill", "M. Harris", "C. Carroll", "P. Crow-Armstrong", "J. Walker", "B. Marsh", "J. Wood", "J. Soto", "K. Tucker", "Joey Ortiz", "K. Schwarber", "S. Imanaga", "S. Alcantara", "M. Boyd", "M. Keller", "A. Abbott", "C. Horton", "M. King", "B. Woodruff", "F. Peralta", "B. Pfaadt", "S. Strider", "P. Skenes", "J. Misiorowski", "Y. Yamamoto", "N. Cortes", "R. Iglesias",  "C. Kelly", "A. Ramirez", "N. Arenado", "M. Busch", "Austin Riley", "P. Smith", "F. Freeman", "M. Machado", "M. Winn", "E. De La Cruz", "D. Swanson", "W. Adames", "S. Frelick", "R. Acuna", "J. Hoo Lee", "V. Scott II", "J. Chourio", "M. Yastrzemski", "S. Suzuki", "D. Crews", "R. Lopez", "N. Lodolo", "C. Cavalli", "G. Holmes", "M. McGreevy", "J. Luzardo", "L. Webb", "C. Sanchez", "C. Sale", "N. Pivetta", "J. Taillon", "R. Ray", "B. Singer", "S. Ohtani", "William Contreras", "Daylen Lile", "Fernando Tatis", "Mookie Betts", "Ketel Marte", "Marcus Semien", "Bryce Harper", "Bo Bichette", "Ozzie Albies", "Eugenio Suarez", "Austin Riley", "Miguel Rojas", "Alex Bregman", "Blake Snell", "Zac Gallen", "Mason Miller", "Otto Lopez", "Ezekiel Tovar", "Matt Chapman", "Alex Bohm", "Matt Olson", "Kyle Stowers", "Tyler Glasnow", "Will Smith", "Edwin Diaz", "Luis Garcia", "Eury Perez", "Luis Robert", "Brandon Lowe", "Devin Williams", "Ian Happ", "Aaron Nola", "TJ Friedl", "Jhoan Duran", "Xander Bogaerts", "Rafael Devers", "Merrill Kelly", "Jorge Polanco", "Mickey Moniak", "Zack Wheeler", "Emmet Sheehan", "Teoscar Hernandez", "Daniel Palencia", "Spencer Steer", "Brenton Doyle", "Bryson Stott", "Joe Musgrove", "Carlos Santana", "JT Realmuto", "Trevor Megill", "Miguel Amaya", "Oneil Cruz", "Christian Yelich", "Luis Arraez", "Jakob Marsee", "Noelvi Marte", "Liam Hicks", "Hunter Greene", "Emilio Pagan", "Ryan O'Hearn", "Andy Pages", "Bryan Reynolds", "Freddy Fermin", "Matt McLain", "Ryan Walker", "Tyler Stephenson", "Tanner Scott", "Edward Cabrera", "Patrick Bailey", "Heliot Ramos", "Adolis Garcia", "Andrew Vaughn", "Tommy Edman", "Matt Svanson", "Pete Fairbanks", "Brett Baty", "Dennis Santana", "Tyler Freeman", "Ramon Laureano", "Jordan Beck", "Willy Castro", "Conor Norby", "Joey Wentz", "Kevin Ginkel", "Kodai Senga", "Tyler Mahle", "Abner Uribe", "Robert Suarez", "Ryne Nelson", "Nolan Gorman", "Kyle Karros", "Ben Brown", "Tobias Myers", "Quinn Priester", "Lourdes Gurriel", "Matt Shaw", "Gavin Sheets", "Jake Cronenworth", "Eduardo Rodriguez", "Luis Torrens", "Sean Manaea", "Dustin May", "Jake Mangum", "Marcell Ozuna", "Garrett Mitchell", "TJ Rumfield", "David Peterson", "Mark Vientos", "Keibert Ruiz", "Joey Bart", "Joseph Ortiz", "Brady House", "Harrison Bader", "Max Meyer", "Matthew Liberatore", "Mike Tauchman", "Chad Patrick", "Henry Davis", "Braxton Ashcraft", "Lars Nootbaar", "Jake McCarthy", "Jorge Mateo", "Alex Vesia", "Nick Castellanos", "Corbin Burnes", "Luke Weaver", "Jaxon Wiggins", "Riley O'Brien", "Clay Holmes", "Spencer Schwellenbach"],
  "players": []
}

def test_5(client):
    response = client.post(
        "/value",
        json=data5,
        headers={
            "X-API-KEY": os.environ.get("API_KEY")
        }
    )

    assert response.status_code == 200

    data = response.get_json()
    assert "results" in data
    print(data["results"][:10])
