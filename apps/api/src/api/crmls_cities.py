# Canonical set of CRMLS-covered cities across 6 SoCal counties.
# Kept in sync with apps/web/lib/crmls-cities.ts on the frontend.

VALID_CITY_NAMES: set[str] = {
    # ─── Los Angeles County ───
    "Agoura Hills", "Alhambra", "Altadena", "Arcadia", "Artesia", "Avalon",
    "Azusa", "Baldwin Park", "Bell", "Bell Gardens", "Bellflower",
    "Beverly Hills", "Bradbury", "Burbank", "Calabasas", "Carson",
    "Cerritos", "Claremont", "Commerce", "Compton", "Covina", "Cudahy",
    "Culver City", "Diamond Bar", "Downey", "Duarte", "East Los Angeles",
    "El Monte", "El Segundo", "Gardena", "Glendale", "Glendora",
    "Hacienda Heights", "Hawaiian Gardens", "Hawthorne", "Hermosa Beach",
    "Hidden Hills", "Huntington Park", "Industry", "Inglewood", "Irwindale",
    "La Cañada Flintridge", "La Crescenta-Montrose", "La Habra Heights",
    "La Mirada", "La Puente", "La Verne", "Lakewood", "Lancaster",
    "Lawndale", "Lomita", "Long Beach", "Los Angeles", "Lynwood", "Malibu",
    "Manhattan Beach", "Marina del Rey", "Maywood", "Monrovia", "Montebello",
    "Monterey Park", "Norwalk", "Palmdale", "Palos Verdes Estates",
    "Paramount", "Pasadena", "Pico Rivera", "Pomona", "Rancho Palos Verdes",
    "Redondo Beach", "Rolling Hills", "Rolling Hills Estates", "Rosemead",
    "Rowland Heights", "San Dimas", "San Fernando", "San Gabriel",
    "San Marino", "Santa Clarita", "Santa Fe Springs", "Santa Monica",
    "Sierra Madre", "Signal Hill", "South El Monte", "South Gate",
    "South Pasadena", "Temple City", "Topanga", "Torrance", "Vernon",
    "View Park-Windsor Hills", "Walnut", "Walnut Park", "West Carson",
    "West Covina", "West Hollywood", "Westlake Village", "Whittier",
    "Willowbrook",

    # ─── Orange County ───
    "Aliso Viejo", "Anaheim", "Brea", "Buena Park", "Costa Mesa", "Cypress",
    "Dana Point", "Fountain Valley", "Fullerton", "Garden Grove",
    "Huntington Beach", "Irvine", "La Habra", "La Palma", "Laguna Beach",
    "Laguna Hills", "Laguna Niguel", "Laguna Woods", "Lake Forest",
    "Los Alamitos", "Midway City", "Mission Viejo", "Newport Beach",
    "Orange", "Placentia", "Rancho Santa Margarita", "Rossmoor",
    "San Clemente", "San Juan Capistrano", "Santa Ana", "Seal Beach",
    "Stanton", "Trabuco Canyon", "Tustin", "Villa Park", "Westminster",
    "Yorba Linda",

    # ─── Riverside County ───
    "Banning", "Beaumont", "Bermuda Dunes", "Blythe", "Calimesa",
    "Canyon Lake", "Cathedral City", "Coachella", "Corona",
    "Desert Hot Springs", "Eastvale", "French Valley", "Good Hope", "Hemet",
    "Indian Wells", "Indio", "Jurupa Valley", "La Quinta", "Lake Elsinore",
    "Lake Mathews", "Lakeland Village", "Mead Valley", "Menifee",
    "Moreno Valley", "Murrieta", "Norco", "Palm Desert", "Palm Springs",
    "Perris", "Rancho Mirage", "Riverside", "San Jacinto", "Sun City",
    "Temecula", "Temescal Valley", "Thermal", "Thousand Palms", "Wildomar",
    "Winchester",

    # ─── San Bernardino County ───
    "Adelanto", "Apple Valley", "Barstow", "Big Bear Lake", "Bloomington",
    "Chino", "Chino Hills", "Colton", "Crestline", "Devore", "Fontana",
    "Grand Terrace", "Hesperia", "Highland", "Lake Arrowhead", "Loma Linda",
    "Lucerne Valley", "Lytle Creek", "Montclair", "Muscoy", "Needles",
    "Oak Hills", "Ontario", "Phelan", "Rancho Cucamonga", "Redlands",
    "Rialto", "Running Springs", "San Bernardino", "Twentynine Palms",
    "Upland", "Victorville", "Yucaipa", "Yucca Valley",

    # ─── Ventura County ───
    "Bell Canyon", "Camarillo", "Casa Conejo", "Channel Islands Beach",
    "El Rio", "Fillmore", "Meiners Oaks", "Mira Monte", "Moorpark",
    "Newbury Park", "Oak Park", "Oak View", "Ojai", "Oxnard", "Piru",
    "Port Hueneme", "San Buenaventura (Ventura)", "Santa Paula",
    "Simi Valley", "Somis", "Thousand Oaks",

    # ─── San Diego County ───
    "Alpine", "Bonita", "Bonsall", "Borrego Springs", "Cardiff-by-the-Sea",
    "Carlsbad", "Chula Vista", "Coronado", "Del Mar", "El Cajon",
    "Encinitas", "Escondido", "Fallbrook", "Imperial Beach", "Jamul",
    "La Mesa", "Lakeside", "Lemon Grove", "National City", "Oceanside",
    "Poway", "Ramona", "Rancho San Diego", "Rancho Santa Fe", "San Diego",
    "San Marcos", "San Ysidro", "Santee", "Solana Beach", "Spring Valley",
    "Valley Center", "Vista", "Winter Gardens",
}
