import json
from services.valuation import compute_valuation
from services.api_getters import get_teams, get_all_players
from services.helpers import find_player_id

# Test 1 (Before Draft)
data1 = {
  "relevant_stats": [],
  "budget": 182,
  "players_left_to_draft": 16,
  "unavailable_players": ["D. Baldwin", "F. Alvarez", "H. Goodman", "G. Moreno", "S. Horwitz", "R. Mauricio", "M. Muncy", "X. Edwards", "C.J. Abrams", "B. Turang", "T. Turner", "N. Hoerner", "F. Lindor", "G. Perdomo", "A. Burleson", "J. Merrill", "M. Harris", "C. Carroll", "P. Crow-Armstrong", "J. Walker", "B. Marsh", "J. Wood", "J. Soto", "K. Tucker", "Joey Ortiz", "K. Schwarber", "S. Imanaga", "S. Alcantara", "M. Boyd", "M. Keller", "A. Abbott", "C. Horton", "M. King", "B. Woodruff", "F. Peralta", "B. Pfaadt", "S. Strider", "P. Skenes", "J. Misiorowski", "Y. Yamamoto", "N. Cortes", "R. Iglesias",  "C. Kelly", "A. Ramirez", "N. Arenado", "M. Busch", "Austin Riley", "P. Smith", "F. Freeman", "M. Machado", "M. Winn", "E. De La Cruz", "D. Swanson", "W. Adames", "S. Frelick", "R. Acuna", "J. Hoo Lee", "V. Scott II", "J. Chourio", "M. Yastrzemski", "S. Suzuki", "D. Crews", "R. Lopez", "N. Lodolo", "C. Cavalli", "G. Holmes", "M. McGreevy", "J. Luzardo", "L. Webb", "C. Sanchez", "C. Sale", "N. Pivetta", "J. Taillon", "R. Ray", "B. Singer", "S. Ohtani"],
  "players": []
}

def test_1():
    with open("tests/data/players_snapshot.json") as f:
        players = json.load(f)

    data = data1

    result = compute_valuation(players, data)

    assert "results" in result
    assert len(result["results"]) > 0

    print(result["results"][:10])
    
# Test 2 (After Drafting 10 Players)
data2 = {
  "relevant_stats": [],
  "budget": 182,
  "players_left_to_draft": 16,
  "unavailable_players": ["D. Baldwin", "F. Alvarez", "H. Goodman", "G. Moreno", "S. Horwitz", "R. Mauricio", "M. Muncy", "X. Edwards", "C.J. Abrams", "B. Turang", "T. Turner", "N. Hoerner", "F. Lindor", "G. Perdomo", "A. Burleson", "J. Merrill", "M. Harris", "C. Carroll", "P. Crow-Armstrong", "J. Walker", "B. Marsh", "J. Wood", "J. Soto", "K. Tucker", "Joey Ortiz", "K. Schwarber", "S. Imanaga", "S. Alcantara", "M. Boyd", "M. Keller", "A. Abbott", "C. Horton", "M. King", "B. Woodruff", "F. Peralta", "B. Pfaadt", "S. Strider", "P. Skenes", "J. Misiorowski", "Y. Yamamoto", "N. Cortes", "R. Iglesias",  "C. Kelly", "A. Ramirez", "N. Arenado", "M. Busch", "Austin Riley", "P. Smith", "F. Freeman", "M. Machado", "M. Winn", "E. De La Cruz", "D. Swanson", "W. Adames", "S. Frelick", "R. Acuna", "J. Hoo Lee", "V. Scott II", "J. Chourio", "M. Yastrzemski", "S. Suzuki", "D. Crews", "R. Lopez", "N. Lodolo", "C. Cavalli", "G. Holmes", "M. McGreevy", "J. Luzardo", "L. Webb", "C. Sanchez", "C. Sale", "N. Pivetta", "J. Taillon", "R. Ray", "B. Singer", "S. Ohtani", "William Contreras", "Daylen Lile", "Fernando Tatis", "Mookie Betts", "Ketel Marte", "Marcus Semien", "Bryce Harper", "Bo Bichette", "Ozzie Albies", "Eugenio Suarez"],
  "players": []
}

def test_2():
    with open("tests/data/players_snapshot.json") as f:
        players = json.load(f)

    data = data2

    result = compute_valuation(players, data)

    assert "results" in result
    assert len(result["results"]) > 0

    print(result["results"][:10])
    
# Test 3 (After Drafting 50 Players)
data3 = {
  "relevant_stats": [],
  "budget": 33,
  "players_left_to_draft": 7,
  "unavailable_players": ["D. Baldwin", "F. Alvarez", "H. Goodman", "G. Moreno", "S. Horwitz", "R. Mauricio", "M. Muncy", "X. Edwards", "C.J. Abrams", "B. Turang", "T. Turner", "N. Hoerner", "F. Lindor", "G. Perdomo", "A. Burleson", "J. Merrill", "M. Harris", "C. Carroll", "P. Crow-Armstrong", "J. Walker", "B. Marsh", "J. Wood", "J. Soto", "K. Tucker", "Joey Ortiz", "K. Schwarber", "S. Imanaga", "S. Alcantara", "M. Boyd", "M. Keller", "A. Abbott", "C. Horton", "M. King", "B. Woodruff", "F. Peralta", "B. Pfaadt", "S. Strider", "P. Skenes", "J. Misiorowski", "Y. Yamamoto", "N. Cortes", "R. Iglesias",  "C. Kelly", "A. Ramirez", "N. Arenado", "M. Busch", "Austin Riley", "P. Smith", "F. Freeman", "M. Machado", "M. Winn", "E. De La Cruz", "D. Swanson", "W. Adames", "S. Frelick", "R. Acuna", "J. Hoo Lee", "V. Scott II", "J. Chourio", "M. Yastrzemski", "S. Suzuki", "D. Crews", "R. Lopez", "N. Lodolo", "C. Cavalli", "G. Holmes", "M. McGreevy", "J. Luzardo", "L. Webb", "C. Sanchez", "C. Sale", "N. Pivetta", "J. Taillon", "R. Ray", "B. Singer", "S. Ohtani", "William Contreras", "Daylen Lile", "Fernando Tatis", "Mookie Betts", "Ketel Marte", "Marcus Semien", "Bryce Harper", "Bo Bichette", "Ozzie Albies", "Eugenio Suarez", "Austin Riley", "Miguel Rojas", "Alex Bregman", "Blake Snell", "Zac Gallen", "Mason Miller", "Otto Lopez", "Ezekiel Tovar", "Matt Chapman", "Alex Bohm", "Matt Olson", "Kyle Stowers", "Tyler Glasnow", "Will Smith", "Edwin Diaz", "Luis Garcia", "Eury Perez", "Luis Robert", "Brandon Lowe", "Devin Williams", "Ian Happ", "Aaron Nola", "TJ Friedl", "Jhoan Duran", "Xander Bogaerts", "Rafael Devers", "Merrill Kelly", "Jorge Polanco", "Mickey Moniak", "Zack Wheeler", "Emmet Sheehan", "Teoscar Hernandez", "Daniel Palencia", "Spencer Steer", "Brenton Doyle", "Bryson Stott", "Joe Musgrove", "Carlos Santana", "JT Realmuto", "Trevor Megill"],
  "players": []
}

def test_3():
    with open("tests/data/players_snapshot.json") as f:
        players = json.load(f)

    data = data3

    result = compute_valuation(players, data)

    assert "results" in result
    assert len(result["results"]) > 0

    print(result["results"][:10])
    
# Test 4 (After Drafting 100 Players)
data4 = {
  "relevant_stats": [],
  "budget": 1,
  "players_left_to_draft": 1,
  "unavailable_players": ["D. Baldwin", "F. Alvarez", "H. Goodman", "G. Moreno", "S. Horwitz", "R. Mauricio", "M. Muncy", "X. Edwards", "C.J. Abrams", "B. Turang", "T. Turner", "N. Hoerner", "F. Lindor", "G. Perdomo", "A. Burleson", "J. Merrill", "M. Harris", "C. Carroll", "P. Crow-Armstrong", "J. Walker", "B. Marsh", "J. Wood", "J. Soto", "K. Tucker", "Joey Ortiz", "K. Schwarber", "S. Imanaga", "S. Alcantara", "M. Boyd", "M. Keller", "A. Abbott", "C. Horton", "M. King", "B. Woodruff", "F. Peralta", "B. Pfaadt", "S. Strider", "P. Skenes", "J. Misiorowski", "Y. Yamamoto", "N. Cortes", "R. Iglesias",  "C. Kelly", "A. Ramirez", "N. Arenado", "M. Busch", "Austin Riley", "P. Smith", "F. Freeman", "M. Machado", "M. Winn", "E. De La Cruz", "D. Swanson", "W. Adames", "S. Frelick", "R. Acuna", "J. Hoo Lee", "V. Scott II", "J. Chourio", "M. Yastrzemski", "S. Suzuki", "D. Crews", "R. Lopez", "N. Lodolo", "C. Cavalli", "G. Holmes", "M. McGreevy", "J. Luzardo", "L. Webb", "C. Sanchez", "C. Sale", "N. Pivetta", "J. Taillon", "R. Ray", "B. Singer", "S. Ohtani", "William Contreras", "Daylen Lile", "Fernando Tatis", "Mookie Betts", "Ketel Marte", "Marcus Semien", "Bryce Harper", "Bo Bichette", "Ozzie Albies", "Eugenio Suarez", "Austin Riley", "Miguel Rojas", "Alex Bregman", "Blake Snell", "Zac Gallen", "Mason Miller", "Otto Lopez", "Ezekiel Tovar", "Matt Chapman", "Alex Bohm", "Matt Olson", "Kyle Stowers", "Tyler Glasnow", "Will Smith", "Edwin Diaz", "Luis Garcia", "Eury Perez", "Luis Robert", "Brandon Lowe", "Devin Williams", "Ian Happ", "Aaron Nola", "TJ Friedl", "Jhoan Duran", "Xander Bogaerts", "Rafael Devers", "Merrill Kelly", "Jorge Polanco", "Mickey Moniak", "Zack Wheeler", "Emmet Sheehan", "Teoscar Hernandez", "Daniel Palencia", "Spencer Steer", "Brenton Doyle", "Bryson Stott", "Joe Musgrove", "Carlos Santana", "JT Realmuto", "Trevor Megill", "Miguel Amaya", "Oneil Cruz", "Christian Yelich", "Luis Arraez", "Jakob Marsee", "Noelvi Marte", "Liam Hicks", "Hunter Greene", "Emilio Pagan", "Ryan O'Hearn", "Andy Pages", "Bryan Reynolds", "Freddy Fermin", "Matt McLain", "Ryan Walker", "Tyler Stephenson", "Tanner Scott", "Edward Cabrera", "Patrick Bailey", "Heliot Ramos", "Adolis Garcia", "Andrew Vaughn", "Tommy Edman", "Matt Svanson", "Pete Fairbanks", "Brett Baty", "Dennis Santana", "Tyler Freeman", "Ramon Laureano", "Jordan Beck", "Willy Castro", "Conor Norby", "Joey Wentz", "Kevin Ginkel", "Kodai Senga", "Tyler Mahle", "Abner Uribe", "Robert Suarez", "Ryne Nelson", "Nolan Gorman", "Kyle Karros", "Ben Brown", "Tobias Myers", "Quinn Priester", "Lourdes Gurriel", "Matt Shaw", "Gavin Sheets", "Jake Cronenworth", "Eduardo Rodriguez", "Luis Torrens"],
  "players": []
}

def test_4():
    with open("tests/data/players_snapshot.json") as f:
        players = json.load(f)

    data = data4

    result = compute_valuation(players, data)

    assert "results" in result
    assert len(result["results"]) > 0

    print(result["results"][:10])
    
# Test 5 (After Drafting 130 Players)
data5 = {
  "relevant_stats": [],
  "budget": 0,
  "players_left_to_draft": 0,
  "unavailable_players": ["D. Baldwin", "F. Alvarez", "H. Goodman", "G. Moreno", "S. Horwitz", "R. Mauricio", "M. Muncy", "X. Edwards", "C.J. Abrams", "B. Turang", "T. Turner", "N. Hoerner", "F. Lindor", "G. Perdomo", "A. Burleson", "J. Merrill", "M. Harris", "C. Carroll", "P. Crow-Armstrong", "J. Walker", "B. Marsh", "J. Wood", "J. Soto", "K. Tucker", "Joey Ortiz", "K. Schwarber", "S. Imanaga", "S. Alcantara", "M. Boyd", "M. Keller", "A. Abbott", "C. Horton", "M. King", "B. Woodruff", "F. Peralta", "B. Pfaadt", "S. Strider", "P. Skenes", "J. Misiorowski", "Y. Yamamoto", "N. Cortes", "R. Iglesias",  "C. Kelly", "A. Ramirez", "N. Arenado", "M. Busch", "Austin Riley", "P. Smith", "F. Freeman", "M. Machado", "M. Winn", "E. De La Cruz", "D. Swanson", "W. Adames", "S. Frelick", "R. Acuna", "J. Hoo Lee", "V. Scott II", "J. Chourio", "M. Yastrzemski", "S. Suzuki", "D. Crews", "R. Lopez", "N. Lodolo", "C. Cavalli", "G. Holmes", "M. McGreevy", "J. Luzardo", "L. Webb", "C. Sanchez", "C. Sale", "N. Pivetta", "J. Taillon", "R. Ray", "B. Singer", "S. Ohtani", "William Contreras", "Daylen Lile", "Fernando Tatis", "Mookie Betts", "Ketel Marte", "Marcus Semien", "Bryce Harper", "Bo Bichette", "Ozzie Albies", "Eugenio Suarez", "Austin Riley", "Miguel Rojas", "Alex Bregman", "Blake Snell", "Zac Gallen", "Mason Miller", "Otto Lopez", "Ezekiel Tovar", "Matt Chapman", "Alex Bohm", "Matt Olson", "Kyle Stowers", "Tyler Glasnow", "Will Smith", "Edwin Diaz", "Luis Garcia", "Eury Perez", "Luis Robert", "Brandon Lowe", "Devin Williams", "Ian Happ", "Aaron Nola", "TJ Friedl", "Jhoan Duran", "Xander Bogaerts", "Rafael Devers", "Merrill Kelly", "Jorge Polanco", "Mickey Moniak", "Zack Wheeler", "Emmet Sheehan", "Teoscar Hernandez", "Daniel Palencia", "Spencer Steer", "Brenton Doyle", "Bryson Stott", "Joe Musgrove", "Carlos Santana", "JT Realmuto", "Trevor Megill", "Miguel Amaya", "Oneil Cruz", "Christian Yelich", "Luis Arraez", "Jakob Marsee", "Noelvi Marte", "Liam Hicks", "Hunter Greene", "Emilio Pagan", "Ryan O'Hearn", "Andy Pages", "Bryan Reynolds", "Freddy Fermin", "Matt McLain", "Ryan Walker", "Tyler Stephenson", "Tanner Scott", "Edward Cabrera", "Patrick Bailey", "Heliot Ramos", "Adolis Garcia", "Andrew Vaughn", "Tommy Edman", "Matt Svanson", "Pete Fairbanks", "Brett Baty", "Dennis Santana", "Tyler Freeman", "Ramon Laureano", "Jordan Beck", "Willy Castro", "Conor Norby", "Joey Wentz", "Kevin Ginkel", "Kodai Senga", "Tyler Mahle", "Abner Uribe", "Robert Suarez", "Ryne Nelson", "Nolan Gorman", "Kyle Karros", "Ben Brown", "Tobias Myers", "Quinn Priester", "Lourdes Gurriel", "Matt Shaw", "Gavin Sheets", "Jake Cronenworth", "Eduardo Rodriguez", "Luis Torrens", "Sean Manaea", "Dustin May", "Jake Mangum", "Marcell Ozuna", "Garrett Mitchell", "TJ Rumfield", "David Peterson", "Mark Vientos", "Keibert Ruiz", "Joey Bart", "Joseph Ortiz", "Brady House", "Harrison Bader", "Max Meyer", "Matthew Liberatore", "Mike Tauchman", "Chad Patrick", "Henry Davis", "Braxton Ashcraft", "Lars Nootbaar", "Jake McCarthy", "Jorge Mateo", "Alex Vesia", "Nick Castellanos", "Corbin Burnes", "Luke Weaver", "Jaxon Wiggins", "Riley O'Brien", "Clay Holmes", "Spencer Schwellenbach"],
  "players": []
}

def test_5():
    with open("tests/data/players_snapshot.json") as f:
        players = json.load(f)

    data = data5

    result = compute_valuation(players, data)

    assert "results" in result
    assert len(result["results"]) > 0

    print(result["results"][:10])
    
def test_6():
    with open("tests/data/teams.json") as f:
        predata = json.load(f)
    
    results = get_teams(predata)
    
    assert results == {"count":30,"teams":[{"id":109,"name":"Arizona Diamondbacks","abbreviation":"AZ"},{"id":133,"name":"Athletics","abbreviation":"ATH"},{"id":144,"name":"Atlanta Braves","abbreviation":"ATL"},{"id":110,"name":"Baltimore Orioles","abbreviation":"BAL"},{"id":111,"name":"Boston Red Sox","abbreviation":"BOS"},{"id":112,"name":"Chicago Cubs","abbreviation":"CHC"},{"id":145,"name":"Chicago White Sox","abbreviation":"CWS"},{"id":113,"name":"Cincinnati Reds","abbreviation":"CIN"},{"id":114,"name":"Cleveland Guardians","abbreviation":"CLE"},{"id":115,"name":"Colorado Rockies","abbreviation":"COL"},{"id":116,"name":"Detroit Tigers","abbreviation":"DET"},{"id":117,"name":"Houston Astros","abbreviation":"HOU"},{"id":118,"name":"Kansas City Royals","abbreviation":"KC"},{"id":108,"name":"Los Angeles Angels","abbreviation":"LAA"},{"id":119,"name":"Los Angeles Dodgers","abbreviation":"LAD"},{"id":146,"name":"Miami Marlins","abbreviation":"MIA"},{"id":158,"name":"Milwaukee Brewers","abbreviation":"MIL"},{"id":142,"name":"Minnesota Twins","abbreviation":"MIN"},{"id":121,"name":"New York Mets","abbreviation":"NYM"},{"id":147,"name":"New York Yankees","abbreviation":"NYY"},{"id":143,"name":"Philadelphia Phillies","abbreviation":"PHI"},{"id":134,"name":"Pittsburgh Pirates","abbreviation":"PIT"},{"id":135,"name":"San Diego Padres","abbreviation":"SD"},{"id":137,"name":"San Francisco Giants","abbreviation":"SF"},{"id":136,"name":"Seattle Mariners","abbreviation":"SEA"},{"id":138,"name":"St. Louis Cardinals","abbreviation":"STL"},{"id":139,"name":"Tampa Bay Rays","abbreviation":"TB"},{"id":140,"name":"Texas Rangers","abbreviation":"TEX"},{"id":141,"name":"Toronto Blue Jays","abbreviation":"TOR"},{"id":120,"name":"Washington Nationals","abbreviation":"WSH"}]}
    
def test_7():
    with open("tests/data/players_snapshot.json") as f:
        players = json.load(f)
        
    results = find_player_id("Shohei Ohtani", players=players)
    
    assert results == ({'mlbId': 660271, 'fullName': 'Shohei Ohtani', 'currentAge': 31}, None)
    
def test_8():
    with open("tests/data/player_cursor.json") as f:
        cursor = json.load(f)
        
    results = get_all_players(cursor)
    
    assert results.get("count") == 1302
    assert results.get("players")[0]["name"] == "A.J. Ewing"
    
