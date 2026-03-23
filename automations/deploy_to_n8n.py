#!/usr/bin/env python3
"""
Deploy all 6 Onsite Phase 1 automations to n8n as scheduled workflows.

Each workflow = Schedule Trigger → Code Node (JavaScript with all logic).
Creates workflows as INACTIVE so you can review before activating.

Usage:
  python3 deploy_to_n8n.py          # Deploy all 6
  python3 deploy_to_n8n.py 1        # Deploy specific one
  python3 deploy_to_n8n.py --list   # List existing Onsite workflows
"""

import json
import os
import sys
import urllib.request

# Load .env file (same directory as this script)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

N8N_HOST = os.environ.get("N8N_HOST", "https://n8n.srv1184808.hstgr.cloud")
N8N_API_KEY = os.environ["N8N_API_KEY"]

# === SHARED JAVASCRIPT HELPERS ===
# This gets prepended to every Code node
SHARED_JS = r"""
// === ONSITE CONFIG ===
const Z = {
  cid: '%ZOHO_CID%',
  cs: '%ZOHO_CS%',
  rt: '%ZOHO_RT%'
};
const G = {
  k: '%GALLABOX_KEY%',
  s: '%GALLABOX_SECRET%',
  ch: '%GALLABOX_CHANNEL%'
};
const MGR = {Sumit:'918291400026',Akshansh:'919654225317',Dhruv:'918770101822'};
const REPS = {Sunil:'919289602555',Anjali:'917020774603',Bhavya:'919900425676',Mohan:'918220494443',Gayatri:'919993786319',Shailendra:'919589613771','Amit U':'918762879435',Hitangi:'919082286699','Amit Kumar':'916263582436'};
const PRE_SALES = {Jyoti:'918528001207',Shruti:'919084525155'};
const ALL_TEAM = {...REPS, ...PRE_SALES};

// CRM "Deal Owner" field → API name is Leads_Owner (Zoho naming quirk) → short name mapping
const CRM_OWNER_MAP = {
  'Sunil Demo':'Sunil', 'Sunil':'Sunil',
  'Anjali Bajaj':'Anjali', 'Anjali':'Anjali',
  'Bhavya Pattegudde Janappa':'Bhavya', 'Bhavya P Janappa':'Bhavya', 'Pattegudde Janappa':'Bhavya', 'Bhavya':'Bhavya',
  'Mohan C':'Mohan', 'Mohan':'Mohan',
  'Gayatri Surlkar':'Gayatri', 'Gayatri':'Gayatri',
  'Shailendra Gour':'Shailendra', 'Shailendra':'Shailendra',
  'Amit B Udagatti':'Amit U', 'Amit Udagatti':'Amit U', 'Amit Balasaheb Udagatti':'Amit U',
  'Hitangi Arora':'Hitangi', 'Hitangi':'Hitangi',
  'Amit Kumar':'Amit Kumar',
  'Desi Yulia':'Desi', 'Desi':'Desi',
  'Jyoti':'Jyoti', 'Shruti':'Shruti', 'Chadni':'Chadni',
  'Sumit':'Sumit', 'Akshansh':'Akshansh', 'Dhruv':'Dhruv',
  'Team':'Team'
};

// Primary Zoho CRM owner name per rep (Zoho COQL breaks with 3+ OR conditions)
const CRM_PRIMARY = {
  Sunil:'Sunil Demo', Anjali:'Anjali Bajaj', Bhavya:'Bhavya Pattegudde Janappa',
  Mohan:'Mohan C', Gayatri:'Gayatri Surlkar', Shailendra:'Shailendra Gour',
  'Amit U':'Amit Balasaheb Udagatti', Hitangi:'Hitangi Arora', 'Amit Kumar':'Amit Kumar',
  Desi:'Desi Yulia', Jyoti:'Jyoti', Shruti:'Shruti', Chadni:'Chadni',
  Sumit:'Sumit', Akshansh:'Akshansh', Dhruv:'Dhruv'
};

// TEST MODE: set true to send all messages to Dhruv only
const TEST_MODE = false;
const TEST_PHONE = '918770101822';

// MONITOR MODE: CC all messages to Dhruv so he can verify delivery
// Set false once everything is confirmed working
const MONITOR_MODE = true;
const MONITOR_PHONE = '918770101822';

// Date helpers
const pad = n => String(n).padStart(2, '0');
const now = new Date();
const TODAY = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
const yd = new Date(now); yd.setDate(yd.getDate() - 1);
const YESTERDAY = `${yd.getFullYear()}-${pad(yd.getMonth()+1)}-${pad(yd.getDate())}`;
// Premium customer data: [company, city, state, region(IN/ME/AF/SE), category(C/I/M/A/G), amount, is_renewal(0/1), age_months]
const PCUST = [["Tactile Construction","Chennai","Tamil Nadu","IN","C",18500,0,11],["JP Construction","Puducherry","Andaman and Nicobar Islands","IN","C",106200,0,6],["4K sports Infra Pvt Limited","Hyderabad","Andhra Pradesh","IN","C",182900,0,7],["Bhavya Developers","Andhra Pradesh","Andhra Pradesh","IN","C",180000,1,38],["LuxeSpace Living Private Limited","Vijayawada","Andhra Pradesh","IN","G",178180,0,7],["Sree datla construction","Godavari","Andhra Pradesh","IN","C",88500,1,23],["Sri Apoorva cmc llp","Hyderabad","Andhra Pradesh","IN","G",85018,0,7],["Sumanth Homes","Tirupathi","Andhra Pradesh","IN","G",65000,0,20],["Lucentt Architects","Anantapur","Andhra Pradesh","IN","A",65000,1,17],["Lucentt Architects","Anantapur","Andhra Pradesh","IN","A",45902,0,17],["NM CONSTRUCTION AND INTERIORS PRIVA","Vijaywada","Andhra Pradesh","IN","I",27000,1,0],["Olive Leaf Architects and Interiors","Hyderabad","Andhra Pradesh","IN","I",20000,0,45],["NM CONSTRUCTION AND INTERIORS PRIVA","Vijaywada","Andhra Pradesh","IN","I",16402,1,51],["Global Fire Industries","Hyedrabad","Andhra Pradesh","IN","M",5900,1,17],["Nahata Buildcons & Consultancy","West Kameng","Arunachal Pradesh","IN","G",42473,0,13],["MK Brothers","Parasamba","Arunachal Pradesh","IN","G",5000,1,26],["Assam Power Generation Corporation ","Guwahati","Assam","IN","G",69530,1,18],["Parag Associates","","Assam","IN","G",66287,1,21],["Phoenix Enterprise","Sivasagar","Assam","IN","G",42480,0,6],["MAA ENGINEERING & ASSOCIATES","Guwahati","Assam","IN","C",40000,1,30],["DJ Baruah Engineers & Architects","Jorhat-785001","Assam","IN","C",30090,0,7],["MAA ENGINEERING & ASSOCIATES","Guwahati","Assam","IN","C",28084,1,30],["Le decor","Assam","Assam","IN","I",7800,0,48],["Archforum Designs","GOLAGHAT","Assam","IN","I",7500,0,42],["Nanak Luxury Homes","Australia","Australia","IN","G",63119,0,13],["M/S. KUWAR CONSTRUCTION","Darbhanga","Bihar","IN","C",121068,1,19],["AFC India","Ballia","Bihar","IN","G",100000,1,28],["SOLARTIVE TECHNO INDUSTRIES PRIVATE","PATNA","Bihar","IN","G",63720,0,18],["Dharmendra Kumar Yadav Construction","Bihar","Bihar","IN","C",50000,0,23],["M/S. KUWAR CONSTRUCTION","Darbhanga","Bihar","IN","C",50000,0,19],["Vector Home Interior Solution Pvt L","Patna","Bihar","IN","I",7080,0,26],["Kahlon Infra LLP","Chandigarh","Chandigarh","IN","C",150000,1,28],["Kahlon Infra LLP","Chandigarh","Chandigarh","IN","C",17699,0,28],["Shree construction and developers","Ambikapur","Chhattisgarh","IN","C",100000,1,20],["Greenboxbuildcon","Bhilai chhattis","Chhattisgarh","IN","G",86730,1,47],["Build Right Infra","Raipur","Chhattisgarh","IN","C",80000,0,15],["Shankara Enterprises","Raipur","Chhattisgarh","IN","G",75520,0,7],["Mangalmurti group","Raipur","Chhattisgarh","IN","G",64900,0,14],["SHRI VINAYAK CONSTRUCTION","Raipur","Chhattisgarh","IN","C",56640,0,7],["yoga electrical","Balaghat","Chhattisgarh","IN","M",25000,0,44],["Architect Mithlesh Sinha","Raipur","Chhattisgarh","IN","A",12744,0,9],["DHANASVI INFRA","","Dadra and Nagar Haveli and Daman and Diu","IN","C",78666,0,1],["Vanraj Infrastructura","Dadra and Nagrh","Daman and Diu","IN","C",11504,1,53],["Awla Infratech","New delhi","Delhi","IN","C",141600,0,1],["Manchanda Interior","Dwarka","Delhi","IN","I",139200,1,41],["Jetking Engineering","Delhi","Delhi","IN","C",120360,0,4],["STAR ENGINEERING CHEMICALS APPLICAT","Delhi","Delhi","IN","C",88412,0,15],["Solutions INC","Delhi","Delhi","IN","G",82600,0,6],["Reinvent Homes Private Limited","Delhi","Delhi","IN","G",76700,0,10],["SG Designs and Builds Private Limit","South Delhi","Delhi","IN","I",74457,0,11],["Isotect contracts Pvt. Ltd","Delhi","Delhi","IN","G",68425,0,12],["NAS Architects","South East Delh","Delhi","IN","A",67500,1,57],["Sai Fire Appliances Pvt Ltd","Delhi","Delhi","IN","M",53100,0,9],["Manchanda Interior","Dwarka","Delhi","IN","I",45000,1,41],["NAS Architects","South East Delh","Delhi","IN","A",25063,0,57],["Anand Raheja","Goa","Goa","IN","G",75520,1,18],["Soni sawant associates llp","Goa","Goa","IN","G",47082,0,22],["Laksh Builder","Goa","Goa","IN","C",17698,0,27],["Laksh Builder","Goa","Goa","IN","C",17500,1,13],["Mahamaya Builders","","Goa","IN","C",10000,1,34],["SL INFRAA","Surat","Gujarat","IN","C",294000,0,6],["Grishva INFRAPROJECT Llp","Gujarat","Gujarat","IN","C",250560,1,0],["Jyona power","Surat","Gujarat","IN","G",200725,1,15],["JAY KHODIYAR CONSTRUCTION","Gujarat","Gujarat","IN","C",187620,1,18],["SL Enterprises","Surat","Gujarat","IN","G",171567,0,6],["TCC Projects Pvt LTD","Ahmedabad","Gujarat","IN","G",152220,1,32],["Aakshar Electricals","Ahmedabad","Gujarat","IN","M",125316,1,55],["Ideaz Interior Designer and Consult","Gujarat","Gujarat","IN","I",100000,1,27],["Innovation Interior","Gujarat","Gujarat","IN","I",85000,1,15],["Innovation Interior","Gujarat","Gujarat","IN","I",70682,0,15],["Aakshar Electricals","Ahmedabad","Gujarat","IN","M",49900,1,55],["ELECTRO VOLT ELECTRICAL","Surat","Gujarat","IN","M",35190,1,31],["Karman Architects","Vadodra","Gujarat","IN","A",16506,0,17],["Mi Architect and Associates","Ahmedabad","Gujarat","IN","A",12800,0,19],["Alvi pmc consltancy","Surat","Gujarat","IN","A",8000,0,27],["Vidyuth engineers","Bhiwadi","Haryana","IN","C",177590,0,22],["Fab furnishers pvt ltd","Gurugram","Haryana","IN","I",118000,0,4],["SAI DEVELOPZONE PRIVATE LIMITED","Gurugram","Haryana","IN","G",113209,0,8],["M/s Adore Build Projects","Faridabad","Haryana","IN","G",98305,0,5],["Freshpro  Agri Infra Pvt Ltd","Kurukshetra","Haryana","IN","C",94400,0,8],["Gypsum structural india pvt ltd","Gurugram","Haryana","IN","G",90000,0,2],["Gobito Construction India pvt ltd","Gurugram","Haryana","IN","C",88500,0,12],["AANANDAM STUDIO AND DESIGNING LLP","Gurgaon","Haryana","IN","I",60180,0,10],["XTORD DESIGNS PRIVATE LIMITED","Gurugram","Haryana","IN","I",45640,0,51],["SINGH JOT BUILDING LIFTING SERVICE","Haryana","Haryana","IN","M",3500,0,42],["Revolution","Solan","Himachal Pradesh","IN","G",47200,0,2],["Whizkids","Shimla","Himachal Pradesh","IN","G",47200,0,26],["Sanshraya design","palampur","Himachal Pradesh","IN","I",25000,1,24],["ESQ BUILDTECH","Nalagarh","Himachal Pradesh","IN","G",24072,0,16],["Rishi Ranjan Gupta Construction","Kullu","Himachal Pradesh","IN","C",22450,0,27],["Sanshraya design","palampur","Himachal Pradesh","IN","I",18000,0,24],["Akbar Husain Shaikh","Hyderabad","Telangana","IN","G",10000,1,40],["PT High Gate Properties","Kuta, Bali","Indonasia","SE","G",94236,0,3],["PT. Dewata Lestari Konstruksi","Bali","Indonasia","SE","G",74816,0,6],["PT. Lumina Property Group","Bali","Indonasia","SE","G",67410,0,2],["Star Construction","Jakarta","Indonasia","SE","C",15900,0,5],["Cokro Pondasi","","Indonesia","SE","G",45915,0,20],["PT. Umira Sinergi Global","indonesia","Indonesia","SE","G",43790,0,15],["Cokro Pondasi","","Indonesia","SE","G",42035,1,20],["Moona Architect","East Java","Indonesia","SE","A",31806,0,14],["Moona Architect","East Java","Indonesia","SE","A",15903,0,14],["PT. Bali Interior Persada","Bali","Indonesia","SE","I",2913,0,14],["Moona Architect","East Java","Indonesia","SE","A",2550,0,14],["ARFAN MEHMOOD","Jammu","Jammu & Kashmir","IN","G",115050,0,8],["Majid Hussain","Jammu & Kashmir","Jammu & Kashmir","IN","G",72000,1,16],["Majid Hussain","Doda jammu and ","Jammu & Kashmir","IN","G",60416,0,16],["Jannat Jubilant Construction","Jammu","Jammu & Kashmir","IN","C",42480,1,48],["Kay and Q Infrastructures Pvt Ltd","Jammu","Jammu & Kashmir","IN","C",20000,0,16],["KD Infrastructures","Kargil","Jammu & Kashmir","IN","C",18000,0,10],["Kamla Electric Store","Noamundi","Jharkhand","IN","G",302670,1,41],["Vasundhara Builders","Jharkhand","Jharkhand","IN","C",106200,0,10],["Aadityah Infra Projects","Jamshedpur","Jharkhand","IN","C",106200,0,6],["Architek Zone","Jamshedpur","Jharkhand","IN","G",82836,1,19],["Dev International","RANCHI","Jharkhand","IN","G",65051,0,21],["3t Developers","JHARKHAND","Jharkhand","IN","C",53100,1,51],["HR Construction Solutions","Bengaluru","Karnataka","IN","C",300000,0,46],["Srinivasa Earth Movers","Bangalore","Karnataka","IN","G",300000,0,3],["ENEWATE PROJECTS PRIVATE LIMITED","Bangalore","Karnataka","IN","G",145700,0,3],["Nakhsha Builder","Mysuru","Karnataka","IN","C",141600,0,53],["Nakhsha Builder","Mysuru","Karnataka","IN","C",136000,0,53],["Technospan","bangalore","Karnataka","IN","G",120360,1,15],["Cfolios Design and Construction Sol","Karnataka","Karnataka","IN","I",105408,1,50],["Proverk Interior & Construction pri","Bangalore","Karnataka","IN","I",53100,0,8],["UPCOUNTRY DECOR PRIVATE LIMITED","Mohali Sas naga","Karnataka","IN","I",48911,0,18],["Fire Lite Solutions","Bangalore","Karnataka","IN","M",31860,0,8],["Cube Consultants and Buildcon","Bengaluru","Karnataka","IN","A",22000,1,43],["Cube Consultants and Buildcon","Bengaluru","Karnataka","IN","A",21877,0,43],["Fire Army safety solutions","Bengaluru","Karnataka","IN","M",20060,0,26],["Vinay consultant","Chitradura karn","Karnataka","IN","A",10000,0,45],["Dsouza Electricals","Bajpe","Karnataka","IN","M",10000,0,8],["BandM  Infra pvt ltd","kochi","Kerala","IN","C",170000,1,18],["Antony Thomas Contracting Pvt Ltd","Kochi","Kerala","IN","G",142560,0,11],["HARI AND COMPANY","Eramallor","Kerala","IN","G",88500,0,30],["HEDERA HOMES LLP","KANNUR","Kerala","IN","G",84960,1,45],["Oranzai Builders","aluva","Kerala","IN","C",83779,0,10],["EP DISIGIN AND BUILDERS","NILAMBUR","Kerala","IN","C",75520,0,33],["PENTARCH THE TECH DESIGNERS & BUILD","","Kerala","IN","I",50000,1,44],["Turnkey Construction","kerala","Kerala","IN","I",42480,1,45],["Turnkey Construction","","Kerala","IN","I",37642,1,50],["shades architectural asociates","kerala","Kerala","IN","A",23597,0,33],["Aspier architecture company","Thrissur","Kerala","IN","A",19500,1,42],["Alamco Architecture","Kerala","Kerala","IN","A",17700,1,20],["Amazon electrical","Kerala","Kerala","IN","M",15000,0,20],["AIGCC GROUP","","Kuwait","ME","G",80550,1,23],["TAWAZUN UNITED CO","Kuwait","Kuwait","ME","G",33395,0,22],["MSLR Pvt ltd","New delhi","Madhya Pradesh","IN","G",784700,0,1],["Perfect Tech Aids Pvt Ltd","Indore","Madhya Pradesh","IN","G",81715,0,7],["A R Enterprises","","Madhya Pradesh","IN","G",76700,0,10],["Samashthiti Construction","Indore","Madhya Pradesh","IN","C",75000,1,21],["JK Engg an Infra","Bhopal","Madhya Pradesh","IN","C",66000,0,50],["Evoge INFRASTRUCTURE SERVICES PRIVA","Bhopal","Madhya Pradesh","IN","C",60770,0,4],["Hydrantt water and fire solan pvt p","Indore","Madhya Pradesh","IN","M",21800,0,8],["LNT DESIGN &CONSTRUCTION","MP","Madhya Pradesh","IN","I",20000,1,52],["LNT DESIGN &CONSTRUCTION","","Madhya Pradesh","IN","I",17000,1,52],["Outsideln consultants","Indore","Madhya Pradesh","IN","A",12000,1,57],["Hasan and kushal Architect","","Madhya Pradesh","IN","A",7080,1,52],["Design & Build Associates","Jabalpur","Madhya Pradesh","IN","I",6000,0,53],["ONE ROOF ARCHITECTS","Chindwada","Madhya Pradesh","IN","A",5900,1,36],["Rocks & Logs (I) Pvt Ltd","Mumbai","Maharashtra","IN","G",214305,1,15],["Adiraj Construction Company","Pune","Maharashtra","IN","C",197532,1,0],["TRIVIE","Mumbai","Maharashtra","IN","G",173018,0,8],["ulhas enterprises","Nagpur","Maharashtra","IN","G",150000,1,20],["INTEGRATED BUILDINGS |STRUCTURAL & ","Mumbai","Maharashtra","IN","A",132750,0,10],["Chaudhary Enterprises Turnkey India","Mumbai","Maharashtra","IN","I",127000,0,3],["Jasfo Design Pvt Ltd","Mumbai","Maharashtra","IN","I",118000,0,2],["Shivam developer","Pune","Maharashtra","IN","C",105138,1,42],["Innovation Engineering and Construc","Nagpuř","Maharashtra","IN","C",100000,1,28],["Design Discipline","Nagpur","Maharashtra","IN","I",53100,0,1],["M S Architectural Sol","mumbai","Maharashtra","IN","A",50000,0,9],["Rashmi Electrical","MUMBAI","Maharashtra","IN","M",50000,1,16],["Fernandes electricals","NA","Maharashtra","IN","M",35365,0,18],["MS Architectural Solutions","Mumbai","Maharashtra","IN","A",34190,0,20],["TYK Design & Renovation sdn bhd","","Malasiya","SE","I",33448,0,18],["HJ design Studio and Construction","Imphal","Manipur","IN","I",7500,0,47],["Megindia Construction","Shilong","Meghalaya","IN","C",50976,0,8],["MAACHKON","Meghalaya","Meghalaya","IN","G",50976,0,9],["Gauraav Siinghal","Brahmanpara, Tu","Meghalaya","IN","G",31500,0,26],["ALGA Infrastructures","Mizoram","Mizoram","IN","C",10000,1,21],["D&B Enterprise","Mumbai","Maharashtra","IN","G",3540,1,34],["Gadhmai building materials PTV limi","","Nepal","IN","G",15000,0,26],["M/s Bro Engineering Movement","","Nepal","IN","C",15000,1,29],["Axis design and build","Nepal","Nepal","IN","I",14999,0,27],["MKT SALES CORPORATION","Pratap Ganj","New Delhi","IN","G",11000,0,30],["Blueline Urban Projects Limited","lagos","Nigeria","AF","G",147340,0,17],["MACRO ACRES LIMITED","Abuja, Nigeria.","Nigeria","AF","G",84206,0,15],["Manash Company","","Odisa","IN","G",90000,1,47],["Fakir  Charan Sahu","Odisa","Odisa","IN","G",26000,1,27],["Manash Company","","Odisa","IN","G",23599,1,47],["RS Construction","Odisa","Odisa","IN","C",12000,1,50],["Truudreamss Engineering and Service","Odisa","Odisa","IN","C",10619,0,30],["SUSHREESARADA CONSTRUCTION.PVT LTD","","Odisa","IN","C",10618,0,37],["M/s United traders","Keonjhar","Odisha","IN","G",83962,1,22],["Prowintech Solutions Pvt Ltd","Odisa","Odisha","IN","G",81120,0,10],["Manash Company","Odisha","Odisha","IN","G",57624,1,47],["AK Construction","Balangir , Odis","Odisha","IN","C",50000,0,43],["DD ENGINEERING","odisha","Odisha","IN","C",28320,0,1],["BEFIT CONSTRUCTION AND INNOVATION P","Berhampur","Odisha","IN","C",26550,0,1],["Archito design studio","Na","Odisha","IN","I",26000,1,52],["Prachi interior","Bhuvneshwar","Odisha","IN","I",20000,1,25],["Prachi interior","Bhuvneshwar","Odisha","IN","I",10000,0,25],["Sarooj Construction LLC","oman","Oman","ME","C",253198,0,20],["AIGCC GROUP","oman","Oman","SE","G",180500,1,23],["ALPHA POOLS OMAN","Oman","Oman","ME","G",117882,1,26],["Burj Al Abrar Trading and contracti","Muscat","Oman","IN","G",91841,0,20],["Horizon Line Construction","Muscat","Oman","ME","C",66930,1,23],["Janleven Quirante","Philipines","Philipines","SE","G",91905,0,21],["HD Engineering","Guyana South Am","Philippines","IN","C",203071,0,1],["Jericho Aguas","Philippines","Philippines","SE","G",60150,0,21],["JB Infrastructure","Punjab","Punjab","IN","C",57525,1,44],["Gagandeep singh & associates","Amritsar","Punjab","IN","G",55000,1,53],["Sarao engineering&projects Llp","Patiala","Punjab","IN","C",53100,1,30],["DESIGN N' BUILD ARCHITECTS","Chandigarh","Punjab","IN","I",49560,0,9],["Jai Durga Co-operative Society","Punjab","Punjab","IN","G",45666,1,51],["INVICTUS PROIECTS","Punjab","Punjab","IN","G",30570,1,39],["A.G Construction co","MOHALI","Punjab","IN","C",25960,0,52],["GURASEES DESIGNS & HOME SOLUTIONS","","Punjab","IN","I",5780,0,33],["Gogna Architects","Punjab","Punjab","IN","A",5000,0,29],["BBM SPORTS LANDSCAPE - TRADING AND ","qatar","Qatar","ME","G",161733,0,21],["HYDRO MASTER","Doha","Qatar","ME","G",98198,0,26],["V Decor Trading","Doha, Qatar","Qatar","ME","I",86627,0,25],["BBM SPORTS LANDSCAPE - TRADING AND ","qatar","Qatar","ME","G",68954,0,10],["Reidius Infra","","Rajashthan","IN","C",300000,0,35],["Anupam traders","","Rajashthan","IN","G",40000,1,48],["GM Buildcon","Sikar","Rajashthan","IN","G",32000,1,38],["Reidius Infra","","Rajashthan","IN","C",21240,1,35],["SARLA INFRA AND INNOVATIONS","Udaipur","Rajashthan","IN","C",18000,1,49],["Lalchand","","Rajashthan","IN","G",15000,1,39],["ARCHITECTURE AVENUE","Jaipur","Rajashthan","IN","A",10620,1,40],["RM Consultant And Asset Management","Ganganagar","Rajashthan","IN","A",10000,1,33],["Skyfall Construction llp","Udaipur","Rajasthan","IN","C",132750,0,4],["Semantics Infra","udaipur","Rajasthan","IN","C",118000,0,12],["GREEN BRICK PROJECT PRIVATE LIMITED","Jaipur","Rajasthan","IN","G",110000,0,45],["Mahaveer Builder","Udaipur","Rajasthan","IN","C",106200,0,6],["BAGAI BUILDCON LLP","Jaipur","Rajasthan","IN","G",94400,1,21],["SHRIRAM AND COMPANY","JODHPUR","Rajasthan","IN","G",76700,0,43],["Akash Interiors","Jaipur","Rajasthan","IN","I",45135,0,4],["Taher Interior decoration","Dangapur","Rajasthan","IN","I",21240,1,37],["Aksa Interiors","udaipur","Rajasthan","IN","I",7630,0,26],["Greystone Contracting LTD","","Saudi Arabia","ME","G",283000,0,25],["T&I Construction","SAR","Saudi Arabia","ME","C",205461,1,19],["1. Thawabit Al Jazeera Contracting ","","Saudi Arabia","ME","G",195699,0,16],["Alam almasih general contracting co","Riyadh","Saudi Arabia","ME","G",182832,0,6],["T&I Construction","SAR","Saudi Arabia","ME","C",167322,0,19],["Awtar construction for general cont","Saudi Arabia","Saudi Arabia","ME","C",140832,0,21685],["C4C Civils","","South Africa","AF","C",41421,0,7],["ADDRESS DEVELOPERS","Coimbatore","Tamil Nadu","IN","C",300000,1,16],["Theeran and co","na","Tamil Nadu","IN","G",250000,1,36],["Sri Ezhumalaiyan Constructions","Nagapattinam","Tamil Nadu","IN","C",198240,0,28],["Booshnam Associates Pvt Ltd","Chennai","Tamil Nadu","IN","G",128854,0,11],["Jaymithran Infrastructures llp","Coimbatore","Tamil Nadu","IN","C",120000,0,1],["Blend Infra-Interiors","Periyakuppam","Tamil Nadu","IN","I",82600,0,7],["BARA PROJECTS","Chennai 600095","Tamil Nadu","IN","G",82600,0,7],["Amis building consultants Pvt. Ltd.","Chennai","Tamil Nadu","IN","A",75000,0,28],["Design and Craft Infra Pvt Ltd","Chennai","Tamil Nadu","IN","I",65000,0,3],["Spacify Interiors","Chennai","Tamil Nadu","IN","I",65000,0,51],["Am Architects","Ramanathapuram","Tamil Nadu","IN","A",32992,0,15],["Eskay Electricals Pvt ltd","Thanjavur","Tamil Nadu","IN","M",30000,0,10],["Imams Architects(Bryaan Consultancy","Chennai","Tamil Nadu","IN","A",27000,0,12],["NRE INDUSTRIES LLP","Hyderabad","Telangana","IN","G",159300,0,6],["M/S SANDHYA CONSTRUCTIONS","Peddapalli","Telangana","IN","C",143960,0,20],["Star power structural projects llp","Hyderabad","Telangana","IN","G",135000,0,3],["JP ENTERPRISES INDIA PVT LTD","Hyderabad","Telangana","IN","G",118000,0,14],["NHF Infra Pvt Ltd","Hyderabad","Telangana","IN","C",91450,0,9],["Subishi Infra","Hyderabad","Telangana","IN","C",65062,0,51],["Design Nature Art","Hyderabad","Telangana","IN","I",59000,1,26],["Virata Interiors Exteriors","Hyderabad","Telangana","IN","I",31506,0,5],["KVR ELECTRICALS","Hyderabad","Telangana","IN","M",18599,0,23],["GK Contruction","Agartala","Tripura","IN","G",10001,0,7],["Sourav Chaudhuri","Agartala","Tripura","IN","G",8000,0,4],["D N CONSTRUCTIONS","Padmapur","Tripura","IN","C",5900,1,42],["Electro RAK","Dubai","UAE","ME","G",624754,0,5],["Blueline Urban Projects Limited","Nigeria","UAE","ME","G",385779,1,17],["Beyond horizon contracting","Dubai","UAE","ME","G",330330,0,6],["FOLOURGO Construction LLC","Dubai","UAE","ME","C",210166,0,2],["Al mamzar decore cont LLC","dubai","UAE","ME","I",205461,0,23],["Four Square Steel Constructions Con","Dubai","UAE","ME","C",196795,0,13],["Indus Construction LLC","Umm Al Quwain, ","UAE","ME","C",179697,0,26],["Idyllic interiors","Dubai","UAE","ME","I",176955,0,12],["Al mamzar decore cont LLC","UAE","UAE","ME","I",125132,0,23],["Bareilly Development Authority","Bareilly","Uttar Pradesh","IN","G",849600,0,4],["Woodofa Lifestyle Pvt Ltd","Noida","Uttar Pradesh","IN","I",194700,0,15],["FlaktGroup India Pvt Ltd","Greater Noida","Uttar Pradesh","IN","G",160000,0,3],["SCENTRE INFRA AND CONSULTATION LLP","Gautam Budda Na","Uttar Pradesh","IN","C",119745,0,10],["B.K CONSTRUCTION & CO.","Agra","Uttar Pradesh","IN","C",108560,0,6],["M/S Rass Contractor and Engineer","Ghaziabad","Uttar Pradesh","IN","C",80098,0,35],["Swastika Design","Varanasi","Uttar Pradesh","IN","I",55319,0,39],["PARMATMA DESIGN AND BUILD PRIVATE L","Noida","Uttar Pradesh","IN","I",42480,0,26],["Shivaya Fire Protection opc pvt ltd","Banaras","Uttar Pradesh","IN","M",40000,1,43],["Shivaya Fire Protection opc pvt ltd","Banaras","Uttar Pradesh","IN","M",35400,0,43],["Brick Box Architects","Uttar Pradesh","Uttar Pradesh","IN","A",27612,1,56],["Lines N Curves Architectural Consul","Uttar Pradesh","Uttar Pradesh","IN","A",23600,1,53],["Studio Milieu Architects","Noida","Uttar Pradesh","IN","A",23600,1,27],["Murti India","","UttarPradesh","IN","G",33000,0,25],["Raghvendra & Associates","","UttarPradesh","IN","G",10000,1,41],["Murti India","","UttarPradesh","IN","G",7000,0,25],["RT Realtors","Haldwani","Uttarakhand","IN","G",84960,0,15],["SKT Buildcon Pvt Ltd","Uttarakhand","Uttarakhand","IN","G",56640,1,26],["F.M Enterprise","Budgam","Uttarakhand","IN","G",40120,0,24],["Lohaar Engineering and Construction","Kashipur","Uttarakhand","IN","C",27186,0,28],["Livanchal Infraspace LLP","Nanital","Uttarakhand","IN","C",27140,0,6],["Anbu Engineering Services","Srinagar","Uttarakhand","IN","C",20000,1,23],["Salva Interiors","Bhatkal","Uttarakhand","IN","I",11800,1,54],["Soumyadip Ghosh","Jalpaiguri","West Bengal","IN","G",72865,0,2],["Nirmal Sales Corporation","Jabakusum","West Bengal","IN","G",63720,1,48],["Alok Kumar Sarkar","Hooghly","West Bengal","IN","G",63402,1,50],["Infrastyle Ventures","Siliguri","West Bengal","IN","C",48273,0,3],["Ricky Rai Construction","West Bengal","West Bengal","IN","C",35400,1,21],["Shiv Sankalp Construction","bengal","West Bengal","IN","C",31110,0,11],["NEAR ME INTERIORS PRIVATE LIMITED","KOLKATA","West Bengal","IN","I",23600,1,52],["Surman Design and Construction","GOBARDANGA, Nor","West Bengal","IN","I",23482,1,20],["The woodland interior & constructio","Siliguri","West Bengal","IN","I",20000,0,24],["Dfine Homes.","","karnataka","IN","G",24000,1,41],["NUMMBERBOL TRADING HOUSE","","karnataka","IN","G",23600,1,54],["CLASS MYSORE","","karnataka","IN","G",20000,1,38],["MAS Technical Co","","kuwait","ME","G",97686,0,14],["MAS Technical Co","","kuwait","ME","G",66080,0,14]];

let MONTH_START = `${now.getFullYear()}-${pad(now.getMonth()+1)}-01`;
let MONTH_NAME = now.toLocaleString('en-US', {month:'long', year:'numeric'});
let MONTH_END = TODAY;
const DAY_NUM = now.getDate();

// Month parser — detects "feb", "january", "last month" etc. in message text
function parseMonth(text) {
  if (!text) return null;
  const t = text.toLowerCase();
  const months = {jan:0,january:0,feb:1,february:1,mar:2,march:2,apr:3,april:3,may:4,jun:5,june:5,jul:6,july:6,aug:7,august:7,sep:8,september:8,oct:9,october:9,nov:10,november:10,dec:11,december:11};
  // Check "last month"
  if (/\blast\s*month\b/.test(t)) {
    const d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const lastDay = new Date(d.getFullYear(), d.getMonth() + 1, 0);
    return {start:`${d.getFullYear()}-${pad(d.getMonth()+1)}-01`, end:`${lastDay.getFullYear()}-${pad(lastDay.getMonth()+1)}-${pad(lastDay.getDate())}`, name:d.toLocaleString('en-US',{month:'long',year:'numeric'})};
  }
  for (const [key, mo] of Object.entries(months)) {
    if (new RegExp('\\b' + key + '\\b').test(t)) {
      const yr = mo > now.getMonth() ? now.getFullYear() - 1 : now.getFullYear();
      const d = new Date(yr, mo, 1);
      const lastDay = new Date(yr, mo + 1, 0);
      const isCurrentMonth = (mo === now.getMonth() && yr === now.getFullYear());
      return {start:`${yr}-${pad(mo+1)}-01`, end: isCurrentMonth ? TODAY : `${lastDay.getFullYear()}-${pad(lastDay.getMonth()+1)}-${pad(lastDay.getDate())}`, name:d.toLocaleString('en-US',{month:'long',year:'numeric'})};
    }
  }
  return null;
}

function daysAgo(n) {
  const d = new Date(now - n * 86400000);
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
}

// Format INR number: 1234567 → "12,34,567"
function fmtINR(n) {
  const s = String(Math.round(n));
  if (s.length <= 3) return s;
  const last3 = s.slice(-3);
  const rest = s.slice(0, -3);
  return rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + last3;
}

// HTTP helper
const http = this.helpers.httpRequest.bind(this.helpers);

// Get Zoho token (lazy — only fail if actually needed)
let token = null;
async function getToken() {
  if (token) return token;
  const _tb = `grant_type=refresh_token&client_id=${Z.cid}&client_secret=${Z.cs}&refresh_token=${Z.rt}`;
  const _tr = await http({method:'POST', url:'https://accounts.zoho.in/oauth/v2/token', body:_tb, headers:{'Content-Type':'application/x-www-form-urlencoded'}});
  token = (typeof _tr === 'string' ? JSON.parse(_tr) : _tr).access_token;
  return token;
}

// COQL query
async function q(query) {
  try {
    const t = await getToken();
    const r = await http({method:'POST', url:'https://www.zohoapis.in/crm/v7/coql',
      headers:{Authorization:`Zoho-oauthtoken ${t}`, 'Content-Type':'application/json'},
      body: JSON.stringify({select_query: query})});
    return typeof r === 'string' ? JSON.parse(r) : r;
  } catch(e) { return {error: e.message}; }
}

async function qCount(query) {
  const d = await q(query);
  return d?.data?.[0]?.total || d?.data?.[0]?.c || 0;
}

async function qPage(query, max=2000) {
  const all = [];
  for (let off = 0; off < max; off += 200) {
    const d = await q(`${query} LIMIT ${off}, 200`);
    if (d?.data) { all.push(...d.data); if (!d?.info?.more_records) break; }
    else break;
  }
  return all;
}

// Send WhatsApp template (opens 24h session window — needed for first msg of day)
async function waTemplate(phone, name) {
  if (TEST_MODE) { phone = TEST_PHONE; name = 'Dhruv [TEST]'; }
  try {
    return await http({method:'POST', url:'https://server.gallabox.com/devapi/messages/whatsapp',
      headers:{apiKey:G.k, apiSecret:G.s, 'Content-Type':'application/json'},
      body: JSON.stringify({channelId:G.ch, channelType:'whatsapp', recipient:{name, phone},
        whatsapp:{type:'template', template:{templateName:'onsite_morning_kickoff', bodyValues:{'1':name}}}})});
  } catch(e) { return {status:'FAILED', error:e.message}; }
}

// WhatsApp sender (respects TEST_MODE + MONITOR_MODE)
async function wa(phone, msg, name='Team') {
  if (TEST_MODE) { phone = TEST_PHONE; name = 'Dhruv [TEST]'; }
  if (msg.length > 4096) msg = msg.slice(0, 4090) + '\n...';
  try {
    const r = await http({method:'POST', url:'https://server.gallabox.com/devapi/messages/whatsapp',
      headers:{apiKey:G.k, apiSecret:G.s, 'Content-Type':'application/json'},
      body: JSON.stringify({channelId:G.ch, channelType:'whatsapp', recipient:{name, phone},
        whatsapp:{type:'text', text:{body:msg}}})});
    // CC to monitor (skip if already sending to monitor, or in TEST_MODE)
    if (MONITOR_MODE && !TEST_MODE && phone !== MONITOR_PHONE) {
      const monMsg = `[TO: ${name}]\n${msg}`;
      await http({method:'POST', url:'https://server.gallabox.com/devapi/messages/whatsapp',
        headers:{apiKey:G.k, apiSecret:G.s, 'Content-Type':'application/json'},
        body: JSON.stringify({channelId:G.ch, channelType:'whatsapp',
          recipient:{name:'Dhruv [MONITOR]', phone:MONITOR_PHONE},
          whatsapp:{type:'text', text:{body:monMsg.slice(0,4096)}}})});
    }
    return r;
  } catch(e) { return {status:'FAILED', error:e.message}; }
}

async function waAll(team, msg) {
  if (TEST_MODE) { await wa(TEST_PHONE, msg, 'Dhruv [TEST]'); return; }
  for (const [name, phone] of Object.entries(team)) await wa(phone, msg, name);
}
"""

# === AUTOMATION-SPECIFIC JAVASCRIPT ===

AUTO_1_JS = r"""
// === AUTOMATION 1: Hourly Follow-Up Alerts ===
// Runs every hour 8 AM - 8 PM IST Mon-Sat
// PERSONALIZED — each rep gets ONLY their own leads with exact follow-up time
// Managers get full team view grouped by rep

const THREE_DAYS_AGO = daysAgo(3);
const istNow = new Date(now.getTime() + 5.5 * 3600000); // UTC → IST
const currentHour = istNow.getHours();
const nextHourIST = currentHour + 1;

// --- Helper: format Lead_Task datetime → "2:30 PM" ---
function fmtTime(dt) {
  if (!dt) return '';
  const m = String(dt).match(/T(\d{2}):(\d{2})/);
  if (!m) return '';
  let h = parseInt(m[1]), mn = m[2];
  const ap = h >= 12 ? 'PM' : 'AM';
  if (h > 12) h -= 12;
  if (h === 0) h = 12;
  return `${h}:${mn} ${ap}`;
}

// --- Helper: get Deal Owner from Leads_Owner field → short name ---
function getDealOwner(l) {
  const raw = String(l.Leads_Owner || '').trim();
  return CRM_OWNER_MAP[raw] || raw || 'Unassigned';
}

// --- Helper: find rep phone from short name ---
const ALL_PHONES = {...REPS, ...PRE_SALES};
function findRep(shortName) {
  if (!shortName || shortName === 'Team' || shortName === 'Unassigned') return null;
  if (TEST_MODE) return {phone: TEST_PHONE, name: shortName + ' [TEST→Dhruv]'};
  if (ALL_PHONES[shortName]) return {phone: ALL_PHONES[shortName], name: shortName};
  return null;
}

// --- Helper: group leads by Owner short name ---
function groupByOwner(leads) {
  const g = {};
  leads.forEach(l => {
    const o = getDealOwner(l);
    if (!g[o]) g[o] = [];
    g[o].push(l);
  });
  return g;
}

// --- Zoho Queries ---
const hourStart = `${TODAY}T${pad(currentHour)}:00:00+05:30`;
const hourEnd = `${TODAY}T${pad(nextHourIST > 23 ? 23 : nextHourIST)}:00:00+05:30`;

const nextHourLeads = await qPage(
  `SELECT Company, Full_Name, Phone, Email, Lead_Task, Sales_Stage, Lead_Status, Leads_Owner FROM Leads WHERE Lead_Task between '${hourStart}' and '${hourEnd}'`
);

const todayLeads = await qPage(
  `SELECT Company, Full_Name, Phone, Email, Lead_Task, Sales_Stage, Lead_Status, Leads_Owner FROM Leads WHERE Lead_Task between '${TODAY}T00:00:00+05:30' and '${TODAY}T23:59:59+05:30'`
);

let overdueLeads = [];
let urgent = [];
if (currentHour <= 8) {
  overdueLeads = await qPage(
    `SELECT Company, Full_Name, Phone, Email, Lead_Task, Sales_Stage, Lead_Status, Leads_Owner FROM Leads WHERE Lead_Task < '${TODAY}T00:00:00+05:30' and Lead_Task > '2026-01-01T00:00:00+05:30' and Lead_Status not in ('12. Subscribed', '11. Rejected', '10. Not Interested (Not Potential)', 'Junk Lead')`
  );
  urgent = overdueLeads.filter(l => {
    const fu = String(l.Lead_Task || '').slice(0, 10);
    return fu && fu < THREE_DAYS_AGO;
  });
}

// Skip if nothing due in next hour (except 8 AM morning briefing)
if (nextHourLeads.length === 0 && currentHour > 8) {
  return [{ json: { nextHour: 0, skipped: true, hour: currentHour } }];
}

const timeLabel = `${pad(currentHour)}:00 - ${pad(nextHourIST)}:00`;
let sentToReps = 0;

if (currentHour <= 8) {
  // ============ 8 AM MORNING BRIEFING ============

  // --- MANAGER MESSAGE: full team view grouped by rep ---
  const todayByOwner = groupByOwner(todayLeads);
  const overdueByOwner = groupByOwner(overdueLeads);

  let mm = `*MORNING BRIEFING — ${TODAY}*\n\n`;
  mm += `Due Today: *${todayLeads.length}*\n`;
  if (overdueLeads.length) mm += `Overdue: *${overdueLeads.length}*\n`;
  if (urgent.length) mm += `Urgent (>3 days): *${urgent.length}*\n`;
  mm += '\n';

  // Per-rep breakdown
  for (const [owner, leads] of Object.entries(todayByOwner).sort((a,b) => b[1].length - a[1].length)) {
    mm += `*${owner}* — ${leads.length} follow-ups\n`;
    leads.slice(0, 5).forEach(l => {
      const co = l.Company || l.Full_Name || '?';
      const time = fmtTime(l.Lead_Task);
      mm += `  - ${co}${time ? ` @ ${time}` : ''}\n`;
    });
    if (leads.length > 5) mm += `  ...+${leads.length - 5} more\n`;
    mm += '\n';
  }

  if (urgent.length) {
    mm += `*URGENT — Overdue >3 Days:*\n`;
    urgent.slice(0, 8).forEach((l, i) => {
      const co = l.Company || l.Full_Name || '?';
      const owner = getDealOwner(l);
      mm += `${i+1}. ${co} (${owner}) — was due: ${String(l.Lead_Task || '').slice(0, 10)}\n`;
    });
    if (urgent.length > 8) mm += `...+${urgent.length - 8} more\n`;
  }
  mm += `\n_Onsite Pulse_`;
  await waAll(MGR, mm);

  // --- REP MESSAGES: each rep gets ONLY their own leads ---
  for (const [owner, leads] of Object.entries(todayByOwner)) {
    const rep = findRep(owner);
    if (!rep) continue;

    const myOverdue = (overdueByOwner[owner] || []).length;
    let rm = `*Good Morning, ${rep.name}!*\n\n`;
    rm += `You have *${leads.length}* follow-ups today`;
    if (myOverdue) rm += ` + *${myOverdue}* overdue`;
    rm += `:\n\n`;

    leads.slice(0, 12).forEach((l, i) => {
      const co = l.Company || l.Full_Name || '?';
      const time = fmtTime(l.Lead_Task);
      const st = l.Sales_Stage || l.Lead_Status || '';
      const contact = l.Phone || l.Email || '';
      rm += `${i+1}. *${co}*`;
      if (time) rm += ` — *${time}*`;
      if (st) rm += ` (${st})`;
      if (contact) rm += `\n   ${contact}`;
      rm += '\n';
    });
    if (leads.length > 12) rm += `\n...+${leads.length - 12} more in CRM\n`;
    if (myOverdue) rm += `\n${myOverdue} overdue — update these in CRM today!\n`;
    rm += `\n_Onsite Pulse — ${TODAY}_`;
    await wa(rep.phone, rm, rep.name);
    sentToReps++;
  }

} else if (currentHour >= 20) {
  // ============ 8 PM EVENING WRAP-UP (Managers only) ============

  const todayByOwner = groupByOwner(todayLeads);
  const totalReps = Object.keys(todayByOwner).length;

  let mm = `*EVENING WRAP-UP — ${TODAY}*\n\n`;
  mm += `Total follow-ups scheduled today: *${todayLeads.length}*\n`;
  mm += `Across *${totalReps}* deal owners\n\n`;

  mm += `*Per Rep Summary:*\n`;
  for (const [owner, leads] of Object.entries(todayByOwner).sort((a,b) => b[1].length - a[1].length)) {
    mm += `  ${owner}: ${leads.length} follow-ups\n`;
  }

  mm += `\nMake sure all reps updated their remarks in CRM.`;
  mm += `\nTomorrow's follow-ups will be sent at 8 AM.`;
  mm += `\n\n_Onsite Pulse_`;
  await waAll(MGR, mm);

} else {
  // ============ HOURLY NUDGE (9 AM - 7 PM) — Reps only ============

  const nextByOwner = groupByOwner(nextHourLeads);
  const todayByOwner = groupByOwner(todayLeads);

  // --- REP MESSAGES: only reps who have follow-ups in next hour ---
  for (const [owner, leads] of Object.entries(nextByOwner)) {
    const rep = findRep(owner);
    if (!rep) continue;

    const myTodayTotal = (todayByOwner[owner] || []).length;
    let rm = `*${rep.name}, ${leads.length} follow-up${leads.length > 1 ? 's' : ''} due NOW (${timeLabel}):*\n\n`;
    leads.forEach((l, i) => {
      const co = l.Company || l.Full_Name || '?';
      const time = fmtTime(l.Lead_Task);
      const st = l.Sales_Stage || l.Lead_Status || '';
      const contact = l.Phone || l.Email || '';
      rm += `${i+1}. *${co}*`;
      if (time) rm += ` — *${time}*`;
      if (st) rm += ` (${st})`;
      if (contact) rm += `\n   ${contact}`;
      rm += '\n';
    });
    rm += `\n_${myTodayTotal} total follow-ups remaining for you today_`;
    rm += `\n_Onsite Pulse_`;
    await wa(rep.phone, rm, rep.name);
    sentToReps++;
  }
}

return [{ json: { nextHour: nextHourLeads.length, today: todayLeads.length, overdue: overdueLeads.length, hour: currentHour, repsNotified: sentToReps } }];
"""

AUTO_2_JS = r"""
// === AUTOMATION 2: Demo Booked → No Demo Done Alert ===
// Shows Deal Owner on each stuck lead so managers know who to push

const SEVEN_DAYS_AGO = daysAgo(7);
const THREE_DAYS_AGO = daysAgo(3);

const total = await qCount("SELECT COUNT(id) as total FROM Leads WHERE Lead_Status = '6. Demo booked' and Demo_Done_Date is null");

const urgentLeads = await qPage(
  `SELECT Company, Full_Name, Phone, Email, Lead_Assigned_Time, Lead_Source, Leads_Owner FROM Leads WHERE Lead_Status = '6. Demo booked' and Demo_Done_Date is null and Lead_Assigned_Time < '${SEVEN_DAYS_AGO}T00:00:00+05:30'`
);

const warningLeads = await qPage(
  `SELECT Company, Full_Name, Phone, Email, Lead_Assigned_Time, Lead_Source, Leads_Owner FROM Leads WHERE Lead_Status = '6. Demo booked' and Demo_Done_Date is null and Lead_Assigned_Time between '${SEVEN_DAYS_AGO}T00:00:00+05:30' and '${THREE_DAYS_AGO}T23:59:59+05:30'`
);

function dealOwner(l) {
  const raw = String(l.Leads_Owner || '').trim();
  return CRM_OWNER_MAP[raw] || raw || '?';
}

const recent = total - urgentLeads.length - warningLeads.length;

let msg = `*DEMO STUCK ALERT — ${TODAY}*\n\n*${total}* leads in 'Demo Booked' but demo NOT done.\n\nURGENT (>7 days): *${urgentLeads.length}*\nWarning (3-7 days): *${warningLeads.length}*\nRecent (<3 days): *${recent}*\n`;

if (urgentLeads.length) {
  msg += `\n*URGENT — Book or Remove:*\n`;
  urgentLeads.slice(0, 12).forEach((l, i) => {
    const co = l.Company || l.Full_Name || '?';
    const owner = dealOwner(l);
    msg += `${i+1}. *${co}* — _${owner}_`;
    const contact = l.Phone || l.Email || '';
    if (contact) msg += `\n   ${contact}`;
    msg += '\n';
  });
  if (urgentLeads.length > 12) msg += `\n...and ${urgentLeads.length - 12} more urgent\n`;
}

if (warningLeads.length) {
  msg += `\n*WARNING — Follow Up This Week:*\n`;
  warningLeads.slice(0, 8).forEach((l, i) => {
    const co = l.Company || l.Full_Name || '?';
    const owner = dealOwner(l);
    msg += `${i+1}. ${co} — _${owner}_\n`;
  });
  if (warningLeads.length > 8) msg += `\n...and ${warningLeads.length - 8} more\n`;
}

msg += `\nEach demo = Rs.8,305 avg revenue. Don't waste booked demos!`;
msg += `\n\n_Onsite Pulse — ${TODAY}_`;
await waAll(MGR, msg);

return [{ json: { total, urgent: urgentLeads.length, warning: warningLeads.length } }];
"""

AUTO_3_JS = r"""
// === AUTOMATION 3: Daily Rep Scorecard ===
// Step 1: Send morning kickoff template to all reps (opens 24h session window)
// Step 2: Send scorecard data as follow-up message

// --- STEP 1: Send template to all reps first ---
for (const [name, phone] of Object.entries({...REPS, ...ALL_TEAM})) {
  await waTemplate(phone, name);
}
// Also send to managers
for (const [name, phone] of Object.entries(MGR)) {
  await waTemplate(phone, name);
}

// Small delay to let templates deliver before sending data messages
await new Promise(r => setTimeout(r, 3000));

// --- STEP 2: Pull CRM data and send scorecard ---
const totalDemos = await qCount(`SELECT COUNT(id) as total FROM Leads WHERE Demo_Done_Date between '${MONTH_START}' and '${TODAY}'`);
const totalSales = await qCount(`SELECT COUNT(id) as total FROM Leads WHERE Sale_Done_Date between '${MONTH_START}' and '${TODAY}'`);
const vh = await qCount("SELECT COUNT(id) as total FROM Leads WHERE Sales_Stage = 'Very High Prospect'");
const hp = await qCount("SELECT COUNT(id) as total FROM Leads WHERE Sales_Stage = 'High Prospect'");
const demoBooked = await qCount("SELECT COUNT(id) as total FROM Leads WHERE Lead_Status = '6. Demo booked'");
const followupsToday = await qCount(`SELECT COUNT(id) as total FROM Leads WHERE Lead_Task between '${TODAY}T00:00:00+05:30' and '${TODAY}T23:59:59+05:30'`);

// Per Deal Owner demos
const demoLeads = await qPage(`SELECT Leads_Owner, Demo_Done_Date FROM Leads WHERE Demo_Done_Date between '${MONTH_START}' and '${TODAY}'`);
const demoByOwner = {};
demoLeads.forEach(l => {
  const raw = String(l.Leads_Owner || '').trim();
  const owner = CRM_OWNER_MAP[raw] || raw || 'Unknown';
  demoByOwner[owner] = (demoByOwner[owner] || 0) + 1;
});
const sortedOwners = Object.entries(demoByOwner).sort((a, b) => b[1] - a[1]);

// Per Deal Owner sales
const saleLeads = await qPage(`SELECT Leads_Owner, Sale_Done_Date FROM Leads WHERE Sale_Done_Date between '${MONTH_START}' and '${TODAY}'`);
const salesByOwner = {};
saleLeads.forEach(l => {
  const raw = String(l.Leads_Owner || '').trim();
  const owner = CRM_OWNER_MAP[raw] || raw || 'Unknown';
  salesByOwner[owner] = (salesByOwner[owner] || 0) + 1;
});

// Manager message
let mm = `*DAILY SCORECARD — ${TODAY}*\nDay ${DAY_NUM} of ${MONTH_NAME}\n\n`;
mm += `*Team MTD:*\nDemos: *${totalDemos}*\nSales: *${totalSales}*\n\n`;
mm += `*Pipeline:*\nVH Prospects: ${vh}\nHigh Prospects: ${hp}\nDemo Booked: ${demoBooked}\nFollow-ups Today: ${followupsToday}\n\n`;
if (sortedOwners.length) {
  mm += `*MTD by Deal Owner:*\n`;
  sortedOwners.slice(0, 15).forEach(([owner, demoCount]) => {
    const saleCount = salesByOwner[owner] || 0;
    mm += `  ${owner}: ${demoCount} demos`;
    if (saleCount) mm += ` | ${saleCount} sales`;
    mm += '\n';
  });
}
mm += `\n_Onsite Pulse_`;
await waAll(MGR, mm);

// Rep message — no change, generic team motivation
const rm = `*Good Morning! Day ${DAY_NUM} of ${MONTH_NAME}*\n\n*Team so far:* ${totalDemos} demos | ${totalSales} sales\n\n*Today's Focus:*\n- ${followupsToday} follow-ups due today\n- ${demoBooked} demos pending in pipeline\n- ${vh + hp} hot prospects waiting\n\nCheck your CRM follow-up dates. Update remarks after every demo.\n\n_Onsite Pulse — ${TODAY}_`;
await waAll(ALL_TEAM, rm);

return [{ json: { demos: totalDemos, sales: totalSales, vh, hp, demoBooked, followups: followupsToday } }];
"""

AUTO_4_JS = r"""
// === AUTOMATION 4: CRM Hygiene Report ===
// Per Deal Owner hygiene breakdown

const demos = await qPage(
  `SELECT Company, Leads_Owner, Business_Type, Price_PItched, Lead_Task, Demo_Done_Date FROM Leads WHERE Demo_Done_Date between '${MONTH_START}' and '${TODAY}'`
);

if (!demos.length) return [{ json: { status: 'no_demos' } }];

const total = demos.length;
let remarksFilled = 0, priceFilled = 0, followupSet = 0;

// Per-rep hygiene tracking
const repHygiene = {};

demos.forEach(d => {
  const raw = String(d.Leads_Owner || '').trim();
  const owner = CRM_OWNER_MAP[raw] || raw || 'Unknown';
  if (!repHygiene[owner]) repHygiene[owner] = {total: 0, remarks: 0, price: 0, followup: 0};
  repHygiene[owner].total++;

  const remark = d.Business_Type;
  const hasRemark = remark && String(remark).trim() && !['null','None'].includes(String(remark).trim());
  const hasPrice = d.Price_PItched != null;
  const hasFollowup = d.Lead_Task != null;

  if (hasRemark) { remarksFilled++; repHygiene[owner].remarks++; }
  if (hasPrice) { priceFilled++; repHygiene[owner].price++; }
  if (hasFollowup) { followupSet++; repHygiene[owner].followup++; }
});

const rPct = total ? Math.floor(remarksFilled * 100 / total) : 0;
const pPct = total ? Math.floor(priceFilled * 100 / total) : 0;
const fPct = total ? Math.floor(followupSet * 100 / total) : 0;

let msg = `*CRM HYGIENE REPORT — ${MONTH_NAME}*\n\nTotal Demos: *${total}*\n\n`;
msg += `*Team Data Completeness:*\n`;
msg += `Remarks: ${remarksFilled}/${total} (${rPct}%) ${rPct >= 80 ? 'OK' : 'NEEDS WORK'}\n`;
msg += `Price Pitched: ${priceFilled}/${total} (${pPct}%) ${pPct >= 80 ? 'OK' : 'NEEDS WORK'}\n`;
msg += `Follow-up Set: ${followupSet}/${total} (${fPct}%) ${fPct >= 80 ? 'OK' : 'NEEDS WORK'}\n`;

// Per-rep hygiene leaderboard
msg += `\n*Per Rep Hygiene:*\n`;
const sorted = Object.entries(repHygiene).sort((a, b) => {
  const aScore = a[1].total ? (a[1].remarks + a[1].price + a[1].followup) / (a[1].total * 3) : 0;
  const bScore = b[1].total ? (b[1].remarks + b[1].price + b[1].followup) / (b[1].total * 3) : 0;
  return bScore - aScore;
});
sorted.slice(0, 12).forEach(([owner, h]) => {
  const score = h.total ? Math.floor((h.remarks + h.price + h.followup) * 100 / (h.total * 3)) : 0;
  msg += `  ${owner}: ${score}% (${h.total} demos)\n`;
});

msg += `\n*Target:* 80%+ on all three fields.\n\n_Onsite Pulse — ${TODAY}_`;
await waAll(MGR, msg);

return [{ json: { total, remarksPct: rPct, pricePct: pPct, followupPct: fPct } }];
"""

AUTO_5_JS = r"""
// === AUTOMATION 5: Website + WhatsApp Hot Lead Alert ===
// Shows Deal Owner on each lead. Managers get full list, reps get only their own.

const THREE_DAYS_AGO = daysAgo(3);
const allHot = [];

for (const source of ['2.Website', '4.Customer Support WA']) {
  const leads = await qPage(
    `SELECT Company, Full_Name, Phone, Email, Lead_Source, Lead_Status, Leads_Owner, Created_Time FROM Leads WHERE Lead_Source = '${source}' and Created_Time > '${THREE_DAYS_AGO}T00:00:00+05:30' and Demo_Done_Date is null and Lead_Status not in ('12. Subscribed', '11. Rejected', '10. Not Interested (Not Potential)', 'Junk Lead')`
  );
  leads.forEach(l => { l._src = source.includes('Website') ? 'Website' : 'WhatsApp'; });
  allHot.push(...leads);
}

for (const source of ['8. Client Referral', '3. Inbound Demo Req.']) {
  const leads = await qPage(
    `SELECT Company, Full_Name, Phone, Email, Lead_Source, Lead_Status, Leads_Owner, Created_Time FROM Leads WHERE Lead_Source = '${source}' and Created_Time > '${THREE_DAYS_AGO}T00:00:00+05:30' and Demo_Done_Date is null and Lead_Status not in ('12. Subscribed', '11. Rejected', '10. Not Interested (Not Potential)', 'Junk Lead')`
  );
  if (leads.length) {
    leads.forEach(l => { l._src = source.split('.').pop().trim(); });
    allHot.push(...leads);
  }
}

if (!allHot.length) return [{ json: { status: 'no_hot_leads' } }];

function dealOwner(l) {
  const raw = String(l.Leads_Owner || '').trim();
  return CRM_OWNER_MAP[raw] || raw || 'Unassigned';
}

// Count by source
const bySource = {};
allHot.forEach(l => { bySource[l._src] = (bySource[l._src] || 0) + 1; });

// Manager message — full list with Deal Owner
let msg = `*HOT LEAD ALERT — ${TODAY}*\n\n*${allHot.length}* high-converting leads NOT YET contacted:\n\n`;
Object.entries(bySource).sort((a,b) => b[1]-a[1]).forEach(([src, cnt]) => { msg += `*${src}:* ${cnt} leads\n`; });
msg += `\nThese convert *2-3x better* than paid ads.\n\n`;
msg += `*Top Leads:*\n`;
allHot.slice(0, 12).forEach((l, i) => {
  const co = l.Company || l.Full_Name || '?';
  const owner = dealOwner(l);
  msg += `${i+1}. *${co}* (${l._src}) — _${owner}_`;
  const contact = l.Phone || l.Email || '';
  if (contact) msg += `\n   ${contact}`;
  msg += '\n';
});
if (allHot.length > 12) msg += `\n...and ${allHot.length - 12} more in CRM\n`;
msg += `\n_Onsite Pulse_`;
await waAll(MGR, msg);

// Per-rep: each rep gets only their own hot leads
const ALL_PHONES = {...REPS, ...PRE_SALES};
const byOwner = {};
allHot.forEach(l => {
  const o = dealOwner(l);
  if (!byOwner[o]) byOwner[o] = [];
  byOwner[o].push(l);
});

for (const [owner, leads] of Object.entries(byOwner)) {
  if (!owner || owner === 'Team' || owner === 'Unassigned') continue;
  const phone = ALL_PHONES[owner];
  if (!phone) continue;
  if (TEST_MODE) continue; // skip per-rep in test mode

  let rm = `*${owner}, ${leads.length} hot lead${leads.length > 1 ? 's' : ''} waiting!*\n\n`;
  rm += `These are Website/WhatsApp/Referral leads — they convert 2-3x better.\n\n`;
  leads.slice(0, 8).forEach((l, i) => {
    const co = l.Company || l.Full_Name || '?';
    const contact = l.Phone || l.Email || '';
    rm += `${i+1}. *${co}* (${l._src})`;
    if (contact) rm += `\n   ${contact}`;
    rm += '\n';
  });
  if (leads.length > 8) rm += `\n...+${leads.length - 8} more\n`;
  rm += `\nCall them TODAY!\n_Onsite Pulse_`;
  await wa(phone, rm, owner);
}

return [{ json: { hotLeads: allHot.length, bySource } }];
"""

AUTO_7_JS = r"""
// === AUTOMATION 7: Daily Session Opener ===
// Runs at 7:50 AM IST Mon-Sat (10 min before 8 AM briefing)
// Sends sample_template to open the 24h WhatsApp session window for each rep
// WITHOUT this, text-only messages are blocked by WhatsApp (no active session)
// Excludes: Sumit, Akshansh (managers who don't need this ping)

const SESSION_PHONES = {
  ...REPS,
  ...PRE_SALES,
  Dhruv: MGR.Dhruv  // include Dhruv from managers
};

const results = [];
for (const [name, phone] of Object.entries(SESSION_PHONES)) {
  const r = await waTemplate(phone, name);
  const raw = typeof r === 'string' ? JSON.parse(r) : r;
  results.push({name, status: raw?.status || 'SENT'});
}

const sent = results.filter(r => r.status === 'ACCEPTED').length;
const failed = results.filter(r => r.status !== 'ACCEPTED').length;

return [{ json: { sent, failed, total: results.length, results } }];
"""

AUTO_6_JS = r"""
// === AUTOMATION 6: Ad Fatigue & Dying Campaign Alert ===
// FB Ads config
const FB_TOKEN = '%FB_TOKEN%';
const FB_ACCOUNT = 'act_3176065209371338';
const FB_BASE = 'https://graph.facebook.com/v21.0';
const LAST_7 = daysAgo(7);
const LAST_14 = daysAgo(14);

if (!FB_TOKEN || FB_TOKEN === '%FB_TOKEN%') return [{ json: { error: 'No FB token' } }];

async function fbApi(endpoint, params = {}) {
  params.access_token = FB_TOKEN;
  const qs = Object.entries(params).map(([k,v]) => `${k}=${encodeURIComponent(v)}`).join('&');
  try {
    const r = await http({method:'GET', url:`${FB_BASE}/${endpoint}?${qs}`});
    return typeof r === 'string' ? JSON.parse(r) : r;
  } catch(e) { return {error: e.message}; }
}

// Get active campaigns
const campaigns = await fbApi(`${FB_ACCOUNT}/campaigns`, {
  fields: 'name,status,objective',
  filtering: JSON.stringify([{field:'effective_status',operator:'IN',value:['ACTIVE']}]),
  limit: 50
});

const campList = campaigns?.data || [];
const alerts = [];
const campData = [];

for (const camp of campList) {
  const recent = await fbApi(`${camp.id}/insights`, {
    fields: 'spend,impressions,clicks,actions,cost_per_action_type,frequency',
    time_range: JSON.stringify({since: LAST_7, until: TODAY})
  });
  const previous = await fbApi(`${camp.id}/insights`, {
    fields: 'spend,impressions,clicks,actions,cost_per_action_type,frequency',
    time_range: JSON.stringify({since: LAST_14, until: LAST_7})
  });

  const r = recent?.data?.[0] || {};
  const p = previous?.data?.[0] || {};
  const spendR = parseFloat(r.spend || 0);
  const freqR = parseFloat(r.frequency || 0);

  let leadsR = 0, leadsP = 0, cplR = 0, cplP = 0;
  (r.actions || []).forEach(a => { if (a.action_type === 'lead') leadsR = parseInt(a.value); });
  (r.cost_per_action_type || []).forEach(a => { if (a.action_type === 'lead') cplR = parseFloat(a.value); });
  (p.actions || []).forEach(a => { if (a.action_type === 'lead') leadsP = parseInt(a.value); });
  (p.cost_per_action_type || []).forEach(a => { if (a.action_type === 'lead') cplP = parseFloat(a.value); });

  campData.push({name: camp.name, spend7d: spendR, leads7d: leadsR, cpl7d: cplR, leadsP, cplP, freq: freqR});

  if (cplP > 0 && cplR > 0 && cplR > cplP * 1.3) {
    const pct = Math.floor((cplR - cplP) / cplP * 100);
    alerts.push(`*CPL UP ${pct}%* — ${camp.name}\n  Rs.${cplP.toFixed(0)} → Rs.${cplR.toFixed(0)}`);
  }
  if (freqR > 3.0) alerts.push(`*AUDIENCE FATIGUE* — ${camp.name}\n  Frequency: ${freqR.toFixed(1)} (>3.0 = burnt out)`);
  if (spendR > 1000 && leadsR === 0) alerts.push(`*ZERO LEADS* — ${camp.name}\n  Spent Rs.${spendR.toFixed(0)} in 7 days, 0 leads`);
  if (leadsP > 5 && leadsR < leadsP * 0.5) {
    const pct = Math.floor((leadsP - leadsR) / leadsP * 100);
    alerts.push(`*LEADS DOWN ${pct}%* — ${camp.name}\n  ${leadsP} → ${leadsR} (7-day)`);
  }
}

let msg = `*AD PERFORMANCE ALERT — ${TODAY}*\n\n`;
if (alerts.length) {
  msg += `*${alerts.length} Issues Detected:*\n\n`;
  alerts.forEach((a, i) => { msg += `${i+1}. ${a}\n\n`; });
} else {
  msg += 'No critical issues. All campaigns performing within normal range.\n\n';
}
msg += `*Active Campaigns (7-day):*\n`;
campData.sort((a, b) => b.spend7d - a.spend7d).slice(0, 8).forEach(c => {
  if (c.spend7d > 0) {
    msg += `- ${c.name.slice(0, 30)}: Rs.${c.spend7d.toFixed(0)} spend`;
    msg += c.leads7d > 0 ? ` | ${c.leads7d} leads | Rs.${c.cpl7d.toFixed(0)} CPL` : ' | 0 leads';
    msg += '\n';
  }
});
msg += `\n_Onsite Pulse_`;

// Send to Dhruv + Akshansh only
const adRecipients = {Dhruv: MGR.Dhruv, Akshansh: MGR.Akshansh};
for (const [name, phone] of Object.entries(adRecipients)) await wa(phone, msg, name);

return [{ json: { campaigns: campData.length, alerts: alerts.length } }];
"""



AUTO_8_JS = r"""
// === AUTO 8: INTERACTIVE WHATSAPP BOT ===
// Webhook-triggered — responds when team members reply

const body = $input.first().json.body || $input.first().json;
const msg = (body?.message?.text || body?.text || body?.whatsapp?.text?.body || body?.payload?.text || '').trim();
const senderPhone = (body?.message?.from || body?.from || body?.recipient?.phone || body?.sender?.phone || body?.payload?.source || '').replace(/\+/g, '');
const senderName = body?.message?.name || body?.sender?.name || body?.recipient?.name || '';

// === PHONE WHITELIST — only respond to registered team ===
const ALLOWED = {
  ...REPS, ...PRE_SALES,
  Sumit: MGR.Sumit, Akshansh: MGR.Akshansh, Dhruv: MGR.Dhruv
};
const PHONE_TO_NAME = {};
for (const [name, phone] of Object.entries(ALLOWED)) PHONE_TO_NAME[phone] = name;

const repName = PHONE_TO_NAME[senderPhone];
if (!repName) {
  return [{ json: { status: 'ignored', reason: 'not_authorized', phone: senderPhone } }];
}

if (!msg || msg.length < 1) {
  return [{ json: { status: 'ignored', reason: 'empty_message' } }];
}

const msgLower = msg.toLowerCase();

// === INTENT DETECTION ===
let intent = 'chat';
let dateFilter = null;
const wantsNotes = /\b(note|notes|remark|remarks|description|detail|details)\b/.test(msgLower);
if (/\b(lead.*assign|assign.*lead|new lead|leads.*got|leads.*received|leads.*given|kitne lead|lead.*aaye|lead.*mila)\b/.test(msgLower)) { intent = 'leads_assigned'; }
else if (/\b(demo|demos)\b/.test(msgLower)) intent = 'demos';
else if (/\b(sale|sales|closed|won|conversion|revenue|paisa|kitna kamaya)\b/.test(msgLower)) intent = 'sales';
else if (/\b(pipeline|prospect|hp|vhp|high prospect)\b/.test(msgLower)) intent = 'pipeline';
else if (/\b(follow.?up|pending|overdue|task)\b/.test(msgLower)) intent = 'followups';
else if (/\b(help|kya kar|what can|commands?)\b/.test(msgLower)) intent = 'help';
else if (/\b(hi|hello|hey|good morning|gm|namaste)\b/.test(msgLower)) intent = 'greeting';
else if (/\b(premium.*customer|customer.*premium|reference.*customer|existing.*customer|paid.*user|hamara.*customer|humare.*client|client.*list|customer.*from|customer.*in)\b/.test(msgLower)) intent = 'customer_reference';
else if (/\b(score|rank|leaderboard|position|kahan|standing)\b/.test(msgLower)) intent = 'rank';
else if (/\b(target|goal|kitna|how much)\b/.test(msgLower)) intent = 'target';
else if (wantsNotes) intent = 'notes';
// Date filter for leads_assigned
if (/\byesterday\b/.test(msgLower)) dateFilter = 'yesterday';
else if (/\btoday\b/.test(msgLower)) dateFilter = 'today';
else if (/\bthis week\b/.test(msgLower)) dateFilter = 'this_week';
else if (/\blast week\b/.test(msgLower)) dateFilter = 'last_week';

// === MONTH PARSING — override date range if user mentions a specific month ===
const parsedMonth = parseMonth(msg);
if (parsedMonth) {
  MONTH_START = parsedMonth.start;
  MONTH_END = parsedMonth.end;
  MONTH_NAME = parsedMonth.name;
}

// === CRM OWNER NAME for queries (single primary name — COQL breaks with 3+ OR) ===
const ownerFilter = `Leads_Owner = '${CRM_PRIMARY[repName] || repName}'`;

let reply = '';

// === GREETING ===
if (intent === 'greeting') {
  const greetings = [
    `Hey ${repName}! 🙌 Ready to crush some deals today? Just ask me anything — demos, pipeline, sales. I'm here!`,
    `Good morning ${repName}! ☀️ Your friendly Onsite Pulse bot reporting for duty. Kya chahiye?`,
    `Hello ${repName}! 👋 Pipeline check? Demo count? Sales update? Bas bol do!`,
    `Hey hey ${repName}! 🚀 Aaj ka plan kya hai? Main ready hoon data ke saath!`,
  ];
  reply = greetings[Math.floor(Math.random() * greetings.length)];
}

// === HELP ===
else if (intent === 'help') {
  reply = `*Hey ${repName}! Here's what I can do:* 🤖\n\n` +
    `📊 *"my demos"* — Your demo count this month\n` +
    `💰 *"my sales"* — Your closed deals\n` +
    `🔥 *"my pipeline"* — Your hot prospects\n` +
    `📋 *"my follow-ups"* — Pending follow-ups\n` +
    `🏆 *"my rank"* — Where you stand in the team\n` +
    `🎯 *"my target"* — Monthly target vs actual\n\n` +
    `Just type naturally — Hinglish bhi chalega! 😄\n` +
    `_— Onsite Pulse_`;
}

// === DEMOS ===
else if (intent === 'demos') {
  const demoCount = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);
  const bookedCount = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Lead_Status = '6. Demo booked'`);

  const demoLeads = await qPage(`SELECT Full_Name, Company, Demo_Done_Date FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${MONTH_START}' and '${MONTH_END}' ORDER BY Demo_Done_Date DESC`);

  reply = `*${repName}'s Demos — ${MONTH_NAME}* 📊\n\n`;
  reply += `✅ Demos Done: *${demoCount}*\n`;
  reply += `📅 Demos Booked (pending): *${bookedCount}*\n\n`;

  if (demoLeads.length > 0) {
    reply += `*Recent demos:*\n`;
    demoLeads.slice(0, 5).forEach((l, i) => {
      const name = l.Company || l.Full_Name || '?';
      const date = (l.Demo_Done_Date || '').slice(0, 10);
      reply += `${i+1}. ${name} — ${date}\n`;
    });
    if (demoLeads.length > 5) reply += `...+${demoLeads.length - 5} more\n`;
  }
  reply += `\nKeep going ${repName}! 💪\n_— Onsite Pulse_`;
}

// === SALES ===
else if (intent === 'sales') {
  const salesLeads = await qPage(`SELECT Full_Name, Company, Annual_Revenue, Sale_Done_Date FROM Leads WHERE (${ownerFilter}) AND Sale_Done_Date between '${MONTH_START}' and '${MONTH_END}' ORDER BY Sale_Done_Date DESC`);
  const salesCount = salesLeads.length;
  let totalRevenue = 0;
  salesLeads.forEach(l => { totalRevenue += Number(l.Annual_Revenue) || 0; });

  reply = `*${repName}'s Sales — ${MONTH_NAME}* 💰\n\n`;
  reply += `🏆 Sales Closed: *${salesCount}*\n`;
  reply += `💰 Total Revenue: *Rs. ${fmtINR(totalRevenue)}*\n\n`;

  if (salesLeads.length > 0) {
    reply += `*Closures:*\n`;
    salesLeads.slice(0, 8).forEach((l, i) => {
      const name = l.Company || l.Full_Name || '?';
      const rev = Number(l.Annual_Revenue) || 0;
      reply += `${i+1}. ${name}${rev ? ` — Rs. ${fmtINR(rev)}` : ''}\n`;
    });
    if (salesLeads.length > 8) reply += `...+${salesLeads.length - 8} more\n`;
  }
  reply += salesCount > 0 ? `\nGreat work! Keep the momentum! 🔥` : `\nMonth abhi baaki hai — let's close some! 💪`;
  reply += `\n_— Onsite Pulse_`;
}

// === PIPELINE ===
else if (intent === 'pipeline') {
  const vhp = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = 'Very High Prospect'`);
  const hp = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = 'High Prospect'`);
  const prospect = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = '1. Prospect'`);

  reply = `*${repName}'s Pipeline* 🔥\n\n`;
  reply += `🔴 Very High Prospect: *${vhp}*\n`;
  reply += `🟠 High Prospect: *${hp}*\n`;
  reply += `🟡 Prospect: *${prospect}*\n`;
  reply += `\nTotal hot leads: *${vhp + hp + prospect}*\n`;
  reply += vhp > 0 ? `\n${vhp} VHP leads — follow up TODAY! 🎯` : `\nFocus on converting prospects to HP! 📈`;
  reply += `\n_— Onsite Pulse_`;
}

// === FOLLOW-UPS ===
else if (intent === 'followups') {
  const overdue = await qPage(`SELECT Full_Name, Company, Lead_Task FROM Leads WHERE (${ownerFilter}) AND Lead_Task is not null AND Lead_Task < '${TODAY}T00:00:00+05:30'`);
  const todayTasks = await qPage(`SELECT Full_Name, Company, Lead_Task FROM Leads WHERE (${ownerFilter}) AND Lead_Task >= '${TODAY}T00:00:00+05:30' AND Lead_Task <= '${TODAY}T23:59:59+05:30'`);

  reply = `*${repName}'s Follow-Ups* 📋\n\n`;
  reply += `📅 Due Today: *${todayTasks.length}*\n`;
  reply += `⚠️ Overdue: *${overdue.length}*\n\n`;

  if (todayTasks.length > 0) {
    reply += `*Today's calls:*\n`;
    todayTasks.slice(0, 5).forEach((l, i) => {
      reply += `${i+1}. ${l.Company || l.Full_Name || '?'}\n`;
    });
  }
  if (overdue.length > 0) {
    reply += `\n*Overdue (needs attention):*\n`;
    overdue.slice(0, 3).forEach((l, i) => {
      reply += `${i+1}. ${l.Company || l.Full_Name || '?'} — was due ${(l.Lead_Task || '').slice(0, 10)}\n`;
    });
  }
  reply += `\n_— Onsite Pulse_`;
}

// === RANK ===
else if (intent === 'rank') {
  const allReps = await qPage(`SELECT Leads_Owner, Sale_Done_Date FROM Leads WHERE Sale_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);

  const ranks = {};
  (allReps || []).forEach(r => {
    const owner = CRM_OWNER_MAP[r.Leads_Owner] || r.Leads_Owner;
    ranks[owner] = (ranks[owner] || 0) + 1;
  });

  const sorted = Object.entries(ranks).sort((a, b) => b[1] - a[1]);
  const myRank = sorted.findIndex(([n]) => n === repName) + 1;
  const myCount = ranks[repName] || 0;

  reply = `*Team Leaderboard — ${MONTH_NAME}* 🏆\n\n`;
  sorted.slice(0, 5).forEach(([name, count], i) => {
    const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i+1}.`;
    const marker = name === repName ? ' ← YOU' : '';
    reply += `${medal} ${name}: ${count} sales${marker}\n`;
  });

  if (myRank > 5) reply += `\n...you're at #${myRank} with ${myCount} sales`;
  reply += myRank <= 3 ? `\n\nTop 3! Amazing work ${repName}! 🔥` : `\n\nLet's climb up! Every demo counts 💪`;
  reply += `\n_— Onsite Pulse_`;
}

// === TARGET ===
else if (intent === 'target') {
  const mySales = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sale_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);
  const myDemos = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${MONTH_START}' and '${MONTH_END}'`);
  const daysLeft = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate() - DAY_NUM;

  reply = `*${repName}'s Progress — ${MONTH_NAME}* 🎯\n\n`;
  reply += `📊 Demos Done: *${myDemos}*\n`;
  reply += `💰 Sales Closed: *${mySales}*\n`;
  reply += `📅 Days Left: *${daysLeft}*\n\n`;
  reply += `Conversion Rate: ${myDemos > 0 ? Math.round(mySales / myDemos * 100) : 0}%\n`;
  reply += daysLeft > 15 ? `\nStill plenty of time — keep pushing! 🚀` : `\nFinal stretch! Close those hot leads NOW! 🔥`;
  reply += `\n_— Onsite Pulse_`;
}

// === LEADS ASSIGNED ===
else if (intent === 'leads_assigned') {
  let assignStart, assignEnd, assignLabel;
  if (dateFilter === 'yesterday') {
    assignStart = `${YESTERDAY}T00:00:00+05:30`; assignEnd = `${YESTERDAY}T23:59:59+05:30`; assignLabel = 'Yesterday';
  } else if (dateFilter === 'this_week') {
    const ws = new Date(now); ws.setDate(now.getDate() - now.getDay() + 1);
    assignStart = `${ws.getFullYear()}-${pad(ws.getMonth()+1)}-${pad(ws.getDate())}T00:00:00+05:30`;
    assignEnd = `${TODAY}T23:59:59+05:30`; assignLabel = 'This Week';
  } else if (dateFilter === 'last_week') {
    const ls = new Date(now); ls.setDate(now.getDate() - now.getDay() - 6);
    const le = new Date(now); le.setDate(now.getDate() - now.getDay());
    assignStart = `${ls.getFullYear()}-${pad(ls.getMonth()+1)}-${pad(ls.getDate())}T00:00:00+05:30`;
    assignEnd = `${le.getFullYear()}-${pad(le.getMonth()+1)}-${pad(le.getDate())}T23:59:59+05:30`; assignLabel = 'Last Week';
  } else {
    assignStart = `${TODAY}T00:00:00+05:30`; assignEnd = `${TODAY}T23:59:59+05:30`; assignLabel = 'Today';
  }
  const assignedLeads = await qPage(`SELECT Full_Name, Company, Phone, Mobile, Lead_Source, Lead_Assigned_Time FROM Leads WHERE (${ownerFilter}) AND Lead_Assigned_Time between '${assignStart}' and '${assignEnd}' ORDER BY Lead_Assigned_Time DESC`);
  const count = assignedLeads.length;
  reply = `*${repName}'s Leads Assigned — ${assignLabel}*\n\n`;
  reply += `Total: *${count}* leads\n\n`;
  if (count > 0) {
    assignedLeads.slice(0, 10).forEach((l, i) => {
      const name = l.Full_Name || '?';
      const comp = l.Company ? ` — ${l.Company}` : '';
      const ph = l.Phone || l.Mobile || '';
      const src = l.Lead_Source || '';
      reply += `${i+1}. ${name}${comp}\n`;
      if (ph) reply += `   📞 ${ph}\n`;
      if (src) reply += `   📌 ${src}\n`;
    });
    if (count > 10) reply += `\n...+${count - 10} more\n`;
    const srcMap = {};
    assignedLeads.forEach(l => { const s = l.Lead_Source || 'Unknown'; srcMap[s] = (srcMap[s] || 0) + 1; });
    reply += `\n*By Source:*\n`;
    Object.entries(srcMap).sort((a,b) => b[1] - a[1]).forEach(([s, c]) => { reply += `  ${s}: ${c}\n`; });
  } else {
    reply += `No leads assigned ${assignLabel.toLowerCase()}.\n`;
  }
  reply += `\n_— Onsite Pulse_`;
}

// === CUSTOMER REFERENCE (premium customer lookup) ===
else if (intent === 'customer_reference') {
  const CAT_NAMES = {C:'Construction', I:'Interior', M:'MEP', A:'Consulting', G:'General'};
  const REG_NAMES = {IN:'India', ME:'Middle East', AF:'Africa', SE:'South East Asia'};
  const ml = msgLower;

  // Detect category
  let fCat = null;
  if (/\b(construct|infra|builder|civil|road|bridge|housing)\b/.test(ml)) fCat = 'C';
  else if (/\b(interior|decor|furnish|design|kitchen|modular|wood)\b/.test(ml)) fCat = 'I';
  else if (/\b(mep|electric|plumb|hvac|fire|elevator|lift)\b/.test(ml)) fCat = 'M';
  else if (/\b(architect|consult|pmc)\b/.test(ml)) fCat = 'A';

  // Detect region
  let fReg = null;
  if (/\b(middle east|uae|dubai|oman|qatar|saudi|kuwait|bahrain)\b/.test(ml)) fReg = 'ME';
  else if (/\b(africa|nigeria|kenya|south africa)\b/.test(ml)) fReg = 'AF';
  else if (/\b(south east|indonesia|bali|philipp|malaysia)\b/.test(ml)) fReg = 'SE';

  // Detect state — alias map handles typos, abbreviations, alternate spellings
  const STATE_ALIAS = {
    'rajasthan':'Rajasthan','rajashthan':'Rajasthan','rajastan':'Rajasthan','rajstan':'Rajasthan',
    'maharashtra':'Maharashtra','maharastra':'Maharashtra','maha':'Maharashtra',
    'karnataka':'Karnataka','karnatak':'Karnataka',
    'tamil nadu':'Tamil Nadu','tamilnadu':'Tamil Nadu','tn':'Tamil Nadu',
    'telangana':'Telangana','telengana':'Telangana','hyderabad':'Telangana',
    'andhra pradesh':'Andhra Pradesh','andhra':'Andhra Pradesh','ap':'Andhra Pradesh',
    'uttar pradesh':'Uttar Pradesh','up':'Uttar Pradesh','uttarpradesh':'Uttar Pradesh',
    'madhya pradesh':'Madhya Pradesh','mp':'Madhya Pradesh',
    'gujarat':'Gujarat','gujrat':'Gujarat','gj':'Gujarat',
    'chhattisgarh':'Chhattisgarh','chattisgarh':'Chhattisgarh','cg':'Chhattisgarh','chhatisgarh':'Chhattisgarh',
    'kerala':'Kerala','kl':'Kerala',
    'delhi':'Delhi',
    'punjab':'Punjab','pb':'Punjab',
    'haryana':'Haryana','hr':'Haryana',
    'west bengal':'West Bengal','wb':'West Bengal','bengal':'West Bengal',
    'bihar':'Bihar',
    'jharkhand':'Jharkhand','jh':'Jharkhand',
    'odisha':'Odisha','odisa':'Odisha','orissa':'Odisha',
    'assam':'Assam',
    'goa':'Goa',
    'uttarakhand':'Uttarakhand','uk':'Uttarakhand',
    'himachal pradesh':'Himachal Pradesh','himachal':'Himachal Pradesh','hp':'Himachal Pradesh',
    'jammu':'Jammu & Kashmir','kashmir':'Jammu & Kashmir','jk':'Jammu & Kashmir',
    'chandigarh':'Chandigarh',
    'tripura':'Tripura',
    'manipur':'Manipur',
    'meghalaya':'Meghalaya',
    'mizoram':'Mizoram',
    'uae':'UAE','dubai':'UAE',
    'saudi':'Saudi Arabia','saudi arabia':'Saudi Arabia',
    'oman':'Oman','qatar':'Qatar','kuwait':'Kuwait',
    'indonesia':'Indonesia','indonasia':'Indonasia',
  };
  let fState = null;
  // Try longest alias first (multi-word like "tamil nadu" before "tamil")
  const sortedAliases = Object.keys(STATE_ALIAS).sort((a,b) => b.length - a.length);
  for (const alias of sortedAliases) {
    if (ml.includes(alias)) { fState = STATE_ALIAS[alias]; break; }
  }
  // Also match exact state names from data
  if (!fState) {
    const allStates = [...new Set(PCUST.map(c => c[2]))];
    for (const s of allStates) {
      if (ml.includes(s.toLowerCase())) { fState = s; break; }
    }
  }

  // Detect city (match against data)
  let fCity = null;
  if (!fState) {
    const allCities = [...new Set(PCUST.map(c => c[1]).filter(c => c && c.length > 2))];
    for (const c of allCities) {
      if (ml.includes(c.toLowerCase())) { fCity = c; break; }
    }
  }

  // Filter
  let results = PCUST;
  // Match state with fuzzy — "Rajasthan" also matches "Rajashthan", "Odisha" matches "Odisa"
  if (fState) {
    const fsl = fState.toLowerCase();
    results = results.filter(c => c[2] === fState || c[2].toLowerCase().startsWith(fsl.slice(0,5)));
  }
  if (fCity) results = results.filter(c => c[1].toLowerCase().includes(fCity.toLowerCase()));
  if (fCat) results = results.filter(c => c[4] === fCat);
  if (fReg) results = results.filter(c => c[3] === fReg);

  results = [...results].sort((a,b) => b[5] - a[5]);
  const top = results.slice(0, 5);

  let label = fState || fCity || (fReg ? REG_NAMES[fReg] : null) || 'All';
  if (fCat) label += ' \u2014 ' + CAT_NAMES[fCat];

  if (top.length === 0) {
    reply = 'No premium customers found for "' + label + '".\n\nTry: "premium customers from Maharashtra" or "interior companies Gujarat" or "construction companies middle east"\n\n\u2014 Onsite Pulse';
  } else {
    reply = '*Premium Customers \u2014 ' + label + '*\n\n';
    top.forEach((c, i) => {
      const [comp, city, st, reg, cat, amt, renew, age] = c;
      const cityStr = city ? ' (' + city + ')' : '';
      const status = renew ? '\ud83d\udd04 Renewal' : '\ud83c\udd95 Fresh';
      const ageStr = age >= 24 ? Math.floor(age/12) + 'yr' : age >= 1 ? age + 'mo' : 'New';
      const amtStr = amt >= 100000 ? (amt/100000).toFixed(1) + 'L' : (amt/1000).toFixed(0) + 'K';
      reply += (i+1) + '. *' + comp + '*' + cityStr + '\n';
      reply += '   ' + (fCat ? CAT_NAMES[cat] + ' | ' : '') + '\u20b9' + amtStr + ' | ' + status + ' | ' + ageStr + '\n\n';
    });
    reply += '--- _Copy-paste for client_ ---\n';
    reply += '*Paid Users \u2014 ' + label + '*\n';
    if (fCat) {
      const byCat = {};
      top.forEach(c => { const cn = CAT_NAMES[c[4]]; if (!byCat[cn]) byCat[cn]=[]; byCat[cn].push(c[0]); });
      const catKeys = Object.keys(byCat);
      for (const cat of catKeys) {
        if (catKeys.length > 1) reply += '_' + cat + '_\n';
        byCat[cat].forEach(name => { reply += '\u2022 ' + name + '\n'; });
      }
    } else {
      top.forEach(c => { reply += '\u2022 ' + c[0] + '\n'; });
    }
    reply += '\n_Total ' + label + ' in database: ' + results.length + '_';
    reply += '\n\u2014 Onsite Pulse';
  }
}

// === GENERAL CHAT ===
else {
  const funReplies = [
    `Hey ${repName}! Samajh nahi aaya 😅 Try "my demos", "my sales", "my pipeline", or just say "help"!`,
    `${repName}, main data bot hoon yaar — sales aur demos ke baare mein pooch! Type "help" for options 😄`,
    `Hmm interesting ${repName}... but mujhe sirf sales ki baat samajh aati hai 😂 Try "help"!`,
    `${repName}, mere paas jokes nahi hai but numbers zaroor hai! 📊 Type "my pipeline" or "help"`,
  ];
  reply = funReplies[Math.floor(Math.random() * funReplies.length)];
}

// === SEND REPLY ===
await wa(senderPhone, reply, repName);

return [{ json: { status: 'replied', to: repName, intent, msgLength: msg.length } }];
"""

# === AUTO 9: PULSE CHAT (WEB UI) ===
# Same bot logic as AUTO_8 but for web chat — accepts {name, message}, returns {reply}
# No WhatsApp sending — response goes directly to the chat UI
AUTO_9_JS = r"""
// === AUTO 9: PULSE CHAT — WEB INTERFACE ===
const body = $input.first().json.body || $input.first().json;
const repName = (body?.name || '').trim();
const msg = (body?.message || '').trim();
const pin = (body?.pin || '').trim();

// === PIN AUTH ===
const PINS = {
  Sunil:'2824', Anjali:'1409', Bhavya:'5506', Mohan:'5012',
  Gayatri:'4657', Shailendra:'3286', 'Amit U':'2679', Hitangi:'9935',
  'Amit Kumar':'2424', Jyoti:'7912', Shruti:'1520',
  Sumit:'1488', Akshansh:'2535', Dhruv:'4582'
};

// === ROLES ===
// admin: can see ALL reps' data
// team_lead: can see own + assigned team
// rep: own data only
const ROLES = {
  Dhruv:'admin', Sumit:'admin', Akshansh:'admin',
  Anjali:'team_lead',
  Sunil:'rep', Bhavya:'rep', Mohan:'rep', Gayatri:'rep',
  Shailendra:'rep', 'Amit U':'rep', Hitangi:'rep', 'Amit Kumar':'rep',
  Jyoti:'rep', Shruti:'rep'
};

// team_lead can also see these reps' data
const LEAD_ACCESS = {
  Anjali: ['Jyoti', 'Shruti', 'Chadni']
};

if (!repName || !PINS[repName]) {
  return [{ json: { reply: 'Access denied. Name not recognized.', status: 'auth_failed' } }];
}

// === LOGIN FLOW ===
if (msg === '__login__') {
  if (pin !== PINS[repName]) {
    return [{ json: { reply: 'Wrong PIN. Please try again.', status: 'auth_failed' } }];
  }
  const role = ROLES[repName] || 'rep';
  let welcome = `Hey ${repName}! Welcome to Onsite Pulse.\n\n`;
  welcome += `Ask me about your demos, sales, pipeline, follow-ups, or rank.\n`;
  if (role === 'admin') welcome += `\nAdmin access: You can check any rep's data. Try "Anjali demos" or "team overview".\n`;
  else if (role === 'team_lead') welcome += `\nTeam Lead access: You can also check Jyoti, Shruti, Chadni's data.\n`;
  welcome += `\nOr just tap a quick action below!\n— Onsite Pulse`;
  return [{ json: { reply: welcome, status: 'ok', role } }];
}

if (!msg || msg.length < 1) {
  return [{ json: { reply: `Hey ${repName}! Type something — "my demos", "my sales", "my pipeline", or "help"`, status: 'empty' } }];
}

const myRole = ROLES[repName] || 'rep';
const msgLower = msg.toLowerCase();

// === SUPABASE CONVERSATION MEMORY ===
const SB_URL = '%SUPABASE_URL%';
const SB_KEY = '%SUPABASE_KEY%';
const SB_HEADERS = {'apikey':SB_KEY,'Authorization':`Bearer ${SB_KEY}`,'Content-Type':'application/json','Prefer':'return=minimal'};

// Fetch recent conversation history for this user
async function sbGetHistory(userName, limit=5) {
  try {
    const resp = await http({method:'GET',
      url:`${SB_URL}/rest/v1/pulse_chat_history?user_name=eq.${encodeURIComponent(userName)}&order=created_at.desc&limit=${limit}&select=message,reply,intent,lead_context,created_at`,
      headers:{...SB_HEADERS, 'Prefer':''}});
    const data = typeof resp === 'string' ? JSON.parse(resp) : resp;
    return Array.isArray(data) ? data.reverse() : []; // oldest first
  } catch(e) { return []; }
}

// Store a message + reply
async function sbStore(userName, message, replyText, intent, leadContext) {
  try {
    await http({method:'POST', url:`${SB_URL}/rest/v1/pulse_chat_history`,
      headers:SB_HEADERS,
      body:JSON.stringify({user_name:userName, message, reply:(replyText||'').slice(0,2000), intent, lead_context:leadContext||{}})});
  } catch(e) { /* non-critical — don't break chat if store fails */ }
}

// Fetch conversation history (non-blocking — don't fail if Supabase is down)
let chatHistory = [];
try {
  chatHistory = await sbGetHistory(repName, 5);
} catch(e) { /* Supabase unavailable — continue without memory */ }

// Build conversation context string for AI
let conversationContext = '';
if (chatHistory.length > 0) {
  conversationContext = '\n\nRecent conversation history (oldest to newest):\n';
  chatHistory.forEach(h => {
    conversationContext += `User: ${h.message}\nBot: ${(h.reply||'').slice(0,200)}\nIntent: ${h.intent || '?'}`;
    if (h.lead_context?.lead_name) conversationContext += ` | Lead discussed: ${h.lead_context.lead_name}`;
    if (h.lead_context?.lead_phone) conversationContext += ` (${h.lead_context.lead_phone})`;
    conversationContext += '\n';
  });
}

// === "NEED MORE" — continue last customer_reference query ===
let _refState = null, _refCity = null, _refCat = null, _refReg = null, _refOffset = 0;
if (/^\s*(more|need more|aur|next|agla|aage|continue|aur dikhao|aur do|show more)\s*$/i.test(msg) && chatHistory.length > 0) {
  const lastH = chatHistory[chatHistory.length - 1];
  if (lastH.intent === 'customer_reference' && lastH.lead_context) {
    intent = 'customer_reference';
    _refState = lastH.lead_context.ref_state || null;
    _refCity = lastH.lead_context.ref_city || null;
    _refCat = lastH.lead_context.ref_cat || null;
    _refReg = lastH.lead_context.ref_reg || null;
    _refOffset = (lastH.lead_context.ref_offset || 0) + 5;
  }
}

// === DETECT TARGET REP ===
// Admins can say "Anjali demos", "Bhavya sales", etc.
// Team leads can query their team members
// Reps can only query themselves
const ALL_NAMES = Object.keys(PINS);
let targetRep = repName; // default: self
let queryingOther = false;
let queryingAll = false;

if (/\b(team|all|everyone|sab|sabke|overview)\b/.test(msgLower)) {
  if (myRole === 'admin') { queryingAll = true; }
  else if (myRole === 'team_lead') { queryingAll = true; } // will be scoped to their team
}

if (!queryingAll) {
  for (const name of ALL_NAMES) {
    if (name === repName) continue;
    if (new RegExp('\\b' + name.toLowerCase() + '\\b').test(msgLower)) {
      // Check permission
      if (myRole === 'admin') { targetRep = name; queryingOther = true; break; }
      else if (myRole === 'team_lead' && (LEAD_ACCESS[repName] || []).includes(name)) { targetRep = name; queryingOther = true; break; }
      // Reps trying to see others → deny
      else {
        return [{ json: { reply: `Sorry ${repName}, you can only see your own data. Try "my demos" or "my sales".`, status: 'ok', intent: 'denied' } }];
      }
    }
  }
}

// === AI INTENT DETECTION (Grok 4.1 Fast via OpenRouter) ===
const OR_KEY = '%OPENROUTER_KEY%';

// Fast-path: obvious intents (no AI call needed)
let intent = null;
let wantsNotes = false;
let searchPhone = null;
let searchName = null;
let searchCompany = null;
let aiReply = null;
let dateFilter = null;

if (/^\s*(hi|hello|hey|good morning|gm|namaste|yo)\s*[!.]?\s*$/i.test(msg)) intent = 'greeting';
else if (/^\s*(help|kya kar|what can|commands?)\s*[?]?\s*$/i.test(msg)) intent = 'help';

// For everything else → ask AI (Claude Haiku 4.5 — thinks before classifying)
if (!intent) {
  try {
    const aiResp = await http({
      method: 'POST',
      url: 'https://openrouter.ai/api/v1/chat/completions',
      headers: { 'Authorization': `Bearer ${OR_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'anthropic/claude-haiku-4.5',
        max_tokens: 600,
        temperature: 0,
        messages: [
          { role: 'system', content: `You are the brain of Onsite Pulse, a sales CRM chatbot for Onsite Teams (construction SaaS). The user is "${repName}".

STEP 1 — THINK: Before classifying, reason briefly:
- If the message looks garbled/repeated (common from voice-to-text), figure out what the user ACTUALLY meant. Voice input often produces duplicated words like "can you tell can you tell us today's demos" — the real question is just "tell us today's demos".
- Consider typos, Hinglish, Hindi, slang, abbreviations.
- Look at conversation history for context.

STEP 2 — OUTPUT: After thinking, output a JSON object on a NEW line starting with { :

{
  "cleaned_message": "what the user actually meant in plain English",
  "intent": one of: "demos", "sales", "pipeline", "followups", "rank", "target", "notes", "lead_search", "leads_assigned", "customer_reference", "assistant", "greeting", "help", "chat",
  "target_rep": null or the NAME of the team member the user is asking about (e.g. "Bhavya", "Anjali", "Amit U"). null = asking about themselves,
  "month": null or month name if user mentions a specific month (e.g. "feb", "january", "last month"),
  "date_filter": null or one of "today", "yesterday", "this_week", "last_week" — if user mentions a specific day/time period,
  "wants_notes": true/false,
  "search_phone": null or phone number,
  "search_name": null or lead/company name,
  "search_company": null or company name,
  "ai_reply": null or a short friendly reply if intent is "chat",
  "ref_state": null or state name,
  "ref_city": null or city name,
  "ref_category": null or one of "C" (construction), "I" (interior), "M" (mep), "A" (architect/consulting)
}

Intent definitions:
- demos: anything about demos done, demo count, demo list, presentations given. "today's demos" = demos with date_filter "today"
- sales: sales closed, deals won, revenue. "today sales" = sales with date_filter "today"
- pipeline: prospects, hot leads, VHP/HP, pipeline status
- followups: follow-ups, pending tasks, overdue calls
- rank: leaderboard, ranking, position in team
- target: goals, targets, progress, days left
- notes: remarks, notes, lead details
- lead_search: finding a specific lead by phone, name, or company
- leads_assigned: how many leads assigned/received. About ASSIGNMENT count (Lead_Assigned_Time), NOT pipeline
- customer_reference: existing/premium/paid customers, client references
- assistant: product knowledge, pricing, email drafting, objection handling, competitor comparison, sales strategy, pitch help, demo prep
- greeting: hi, hello, good morning
- help: what can the bot do
- chat: general conversation, jokes, unrelated questions

CRITICAL RULES:
1. ALWAYS set date_filter when user says "today", "aaj", "aaj ka", "yesterday", "kal", "this week", "is hafte". Don't ignore time words!
2. "leads assigned" / "new leads" / "kitne leads" = leads_assigned (NOT pipeline)
3. Voice input creates messy text — ALWAYS clean it first. The real intent is in there.
4. If user says "not march today's" or "I said today not month" — they're correcting you. Set date_filter to "today".
5. User may write in English, Hindi, or Hinglish. Understand all three.
6. If user says "same lead", "that one", "uska" — check conversation history.
7. TARGET_REP DETECTION: If user mentions a team member name (even misspelled like "Bhavaya"="Bhavya", "Anajli"="Anjali"), set target_rep to the correct name. Team members: Sunil, Anjali, Bhavya, Mohan, Gayatri, Shailendra, Amit U, Hitangi, Amit Kumar, Jyoti, Shruti, Sumit, Akshansh, Dhruv. If user says "my demos" or no name → target_rep = null.
8. CONTEXT CARRY-OVER: If user says "what about X" / "and X?" / "same for X" / "uska" / "aur X ka" — carry forward the SAME intent AND date_filter from the previous conversation. E.g. if previous was demos+yesterday, and user says "what about Bhavya" → intent=demos, date_filter=yesterday, target_rep=Bhavya.
9. FOLLOW-UP CONTEXT: If the previous message had a date_filter and the new message references it implicitly (like "and Bhavya?" after "yesterday demos"), INHERIT that date_filter. Don't reset to null.${conversationContext}` },
          { role: 'user', content: msg }
        ]
      })
    });
    const parsed = typeof aiResp === 'string' ? JSON.parse(aiResp) : aiResp;
    const aiText = (parsed?.choices?.[0]?.message?.content || '').trim();
    // Parse JSON from AI response — find the JSON object (may have thinking text before it)
    const jsonMatch = aiText.match(/\{[\s\S]*\}/);
    const jsonStr = jsonMatch ? jsonMatch[0] : aiText.replace(/```json?\n?/g, '').replace(/```/g, '').trim();
    const ai = JSON.parse(jsonStr);
    intent = ai.intent || 'chat';
    wantsNotes = ai.wants_notes || false;
    searchPhone = ai.search_phone || null;
    searchName = ai.search_name || null;
    searchCompany = ai.search_company || null;
    aiReply = ai.ai_reply || null;
    dateFilter = ai.date_filter || null;

    // AI-detected target_rep override (handles garbled voice: "Bhavaya" → "Bhavya")
    if (ai.target_rep) {
      const aiTarget = ai.target_rep;
      // Find matching team member name (case-insensitive)
      const matchedName = ALL_NAMES.find(n => n.toLowerCase() === aiTarget.toLowerCase());
      if (matchedName && matchedName !== repName) {
        // Check permission
        if (myRole === 'admin') {
          targetRep = matchedName;
          queryingOther = true;
        } else if (myRole === 'team_lead' && (LEAD_ACCESS[repName] || []).includes(matchedName)) {
          targetRep = matchedName;
          queryingOther = true;
        }
        // Reps: silently ignore (don't block — they might have said a name casually)
      }
    }

    // AI-detected month override
    if (ai.month) {
      const pm = parseMonth(ai.month);
      if (pm) { MONTH_START = pm.start; MONTH_END = pm.end; MONTH_NAME = pm.name; }
    }
  } catch(e) {
    // AI failed — fallback to basic regex
    intent = 'chat';
    const ml = msgLower;
    if (/\b(lead.*assign|assign.*lead|new lead|leads.*got|leads.*received|leads.*given|kitne lead|lead.*aaye|lead.*mila)\b/.test(ml)) intent = 'leads_assigned';
    else if (/\b(premium.*customer|customer.*premium|reference.*customer|existing.*customer|paid.*user|hamara.*customer|humare.*client|client.*list|customer.*from|customer.*in)\b/.test(ml)) intent = 'customer_reference';
    else if (/\b(demo|demos)\b/.test(ml)) intent = 'demos';
    else if (/\b(sale|sales|closed|won|revenue)\b/.test(ml)) intent = 'sales';
    else if (/\b(pipeline|prospect|hp|vhp)\b/.test(ml)) intent = 'pipeline';
    else if (/\b(follow.?up|pending|overdue)\b/.test(ml)) intent = 'followups';
    else if (/\b(rank|leaderboard|position)\b/.test(ml)) intent = 'rank';
    else if (/\b(target|goal)\b/.test(ml)) intent = 'target';
    else if (/\b(price|pricing|cost|plan|feature|module|write|email|mail|draft|pitch|approach|objection|competitor|compare|close|strategy|help me)\b/.test(ml)) intent = 'assistant';
    wantsNotes = /\b(note|notes|remark|remarks)\b/.test(ml);
    if (/\byesterday\b/.test(ml)) dateFilter = 'yesterday';
    else if (/\btoday\b/.test(ml)) dateFilter = 'today';
    else if (/\bthis week\b/.test(ml)) dateFilter = 'this_week';
    else if (/\blast week\b/.test(ml)) dateFilter = 'last_week';
  }
}

if (queryingAll && intent === 'chat') intent = 'demos';

// === MONTH PARSING (fallback — AI may have already set it) ===
const parsedMonth = parseMonth(msg);
if (parsedMonth) {
  MONTH_START = parsedMonth.start;
  MONTH_END = parsedMonth.end;
  MONTH_NAME = parsedMonth.name;
}

// === DATE FILTER OVERRIDE (today/yesterday/this_week/last_week) ===
let DATE_START = MONTH_START;
let DATE_END = MONTH_END;
let DATE_LABEL = MONTH_NAME;

if (dateFilter) {
  const ist = new Date(new Date().toLocaleString('en-US', {timeZone:'Asia/Kolkata'}));
  const y = ist.getFullYear(), m = ist.getMonth(), d = ist.getDate();

  if (dateFilter === 'today') {
    const todayStr = `${y}-${pad(m+1)}-${pad(d)}`;
    DATE_START = todayStr;
    DATE_END = todayStr;
    DATE_LABEL = 'Today';
  } else if (dateFilter === 'yesterday') {
    const yd = new Date(y, m, d - 1);
    const ydStr = `${yd.getFullYear()}-${pad(yd.getMonth()+1)}-${pad(yd.getDate())}`;
    DATE_START = ydStr;
    DATE_END = ydStr;
    DATE_LABEL = 'Yesterday';
  } else if (dateFilter === 'this_week') {
    const dow = ist.getDay() || 7; // Mon=1
    const mon = new Date(y, m, d - dow + 1);
    DATE_START = `${mon.getFullYear()}-${pad(mon.getMonth()+1)}-${pad(mon.getDate())}`;
    DATE_END = `${y}-${pad(m+1)}-${pad(d)}`;
    DATE_LABEL = 'This Week';
  } else if (dateFilter === 'last_week') {
    const dow = ist.getDay() || 7;
    const prevMon = new Date(y, m, d - dow - 6);
    const prevSun = new Date(y, m, d - dow);
    DATE_START = `${prevMon.getFullYear()}-${pad(prevMon.getMonth()+1)}-${pad(prevMon.getDate())}`;
    DATE_END = `${prevSun.getFullYear()}-${pad(prevSun.getMonth()+1)}-${pad(prevSun.getDate())}`;
    DATE_LABEL = 'Last Week';
  }
}

// === BUILD OWNER FILTER ===
// Uses single primary Zoho name (COQL breaks with 3+ OR conditions)
function buildOwnerFilter(name) {
  const primary = CRM_PRIMARY[name];
  return `Leads_Owner = '${primary || name}'`;
}

let ownerFilter;
let displayName = targetRep;

if (queryingAll) {
  if (myRole === 'admin') {
    // All reps — use IN clause (COQL breaks with 3+ OR conditions)
    const allRepNames = [...Object.keys(REPS), ...Object.keys(PRE_SALES)];
    const inList = allRepNames.map(n => `'${CRM_PRIMARY[n] || n}'`).join(',');
    ownerFilter = `Leads_Owner in (${inList})`;
    displayName = 'Team';
  } else if (myRole === 'team_lead') {
    // Own + team — use IN clause
    const teamNames = [repName, ...(LEAD_ACCESS[repName] || [])];
    const inList = teamNames.map(n => `'${CRM_PRIMARY[n] || n}'`).join(',');
    ownerFilter = `Leads_Owner in (${inList})`;
    displayName = `${repName}'s Team`;
  }
} else {
  ownerFilter = buildOwnerFilter(targetRep);
  displayName = targetRep;
}

let reply = '';

// === GREETING ===
if (intent === 'greeting') {
  const istHour = new Date(new Date().toLocaleString('en-US', {timeZone:'Asia/Kolkata'})).getHours();
  const timeGreet = istHour < 12 ? 'Good morning' : istHour < 17 ? 'Good afternoon' : 'Good evening';
  const greetings = [
    `Hey ${repName}! Ready to crush some deals today? Just ask me anything — demos, pipeline, sales. I'm here!`,
    `${timeGreet} ${repName}! Your friendly Pulse bot reporting for duty. Kya chahiye?`,
    `Hello ${repName}! Pipeline check? Demo count? Sales update? Bas bol do!`,
    `${timeGreet} ${repName}! Aaj ka plan kya hai? Main ready hoon data ke saath!`,
  ];
  reply = greetings[Math.floor(Math.random() * greetings.length)];
}

// === HELP ===
else if (intent === 'help') {
  reply = `Hey ${repName}! Here's everything I can do:\n\n` +
    `CRM DATA:\n` +
    `"my demos" — Demo count this month\n` +
    `"my sales" — Closed deals & revenue\n` +
    `"my pipeline" — Hot prospects (VHP/HP)\n` +
    `"my follow-ups" — Pending follow-ups\n` +
    `"my rank" — Team leaderboard\n` +
    `"my target" — Monthly progress\n` +
    `"my notes" — Recent leads with remarks\n` +
    `"find lead <name/phone>" — Search CRM\n` +
    `"premium customers from <state/city>" — Existing client references\n\n` +
    `SALES ASSISTANT:\n` +
    `"our pricing" — Full pricing breakdown\n` +
    `"write a follow-up email" — Draft emails\n` +
    `"how to pitch this client" — Approach strategy\n` +
    `"handle objection: too expensive" — Rebuttals\n` +
    `"compare with Procore" — Competitor info\n` +
    `"what features in Business+" — Product info\n\n` +
    `Add month: "feb demos", "last month sales"\n` +
    (myRole === 'admin' ? `\nAdmin: "Anjali demos", "team overview", "all sales"\n` : '') +
    (myRole === 'team_lead' ? `\nTeam Lead: "Jyoti demos", "all demos"\n` : '') +
    `Hinglish bhi chalega!\n— Onsite Pulse`;
}

// === DEMOS ===
else if (intent === 'demos') {
  const fields = wantsNotes ? 'Full_Name, Company, Demo_Done_Date, Business_Type, Description' : 'Full_Name, Company, Demo_Done_Date';
  const demoCount = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${DATE_START}' and '${DATE_END}'`);
  const bookedCount = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Lead_Status = '6. Demo booked'`);
  const demoLeads = await qPage(`SELECT ${fields} FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${DATE_START}' and '${DATE_END}' ORDER BY Demo_Done_Date DESC`);

  reply = `${displayName}'s Demos — ${DATE_LABEL}\n\n`;
  reply += `Demos Done: ${demoCount}\n`;
  reply += `Demos Booked (pending): ${bookedCount}\n\n`;

  if (demoLeads.length > 0) {
    const limit = wantsNotes ? 8 : 5;
    reply += wantsNotes ? `Demos with notes:\n` : `Recent demos:\n`;
    demoLeads.slice(0, limit).forEach((l, i) => {
      const name = l.Company || l.Full_Name || '?';
      const date = (l.Demo_Done_Date || '').slice(0, 10);
      reply += `${i+1}. ${name} — ${date}\n`;
      if (wantsNotes) {
        const remark = (l.Business_Type || '').trim();
        const desc = (l.Description || '').trim();
        if (remark) reply += `   Remarks: ${remark.slice(0, 120)}\n`;
        if (desc) reply += `   Notes: ${desc.slice(0, 120)}\n`;
        if (!remark && !desc) reply += `   (no notes)\n`;
      }
    });
    if (demoLeads.length > limit) reply += `...+${demoLeads.length - limit} more\n`;
  }
  reply += `\n— Onsite Pulse`;
}

// === SALES ===
else if (intent === 'sales') {
  const salesFields = wantsNotes ? 'Full_Name, Company, Annual_Revenue, Sale_Done_Date, Business_Type, Description' : 'Full_Name, Company, Annual_Revenue, Sale_Done_Date';
  const salesLeads = await qPage(`SELECT ${salesFields} FROM Leads WHERE (${ownerFilter}) AND Sale_Done_Date between '${DATE_START}' and '${DATE_END}' ORDER BY Sale_Done_Date DESC`);
  const salesCount = salesLeads.length;
  let totalRevenue = 0;
  salesLeads.forEach(l => { totalRevenue += Number(l.Annual_Revenue) || 0; });

  reply = `${displayName}'s Sales — ${DATE_LABEL}\n\n`;
  reply += `Sales Closed: ${salesCount}\n`;
  reply += `Total Revenue: Rs. ${fmtINR(totalRevenue)}\n\n`;

  if (salesLeads.length > 0) {
    reply += `Closures:\n`;
    salesLeads.slice(0, 8).forEach((l, i) => {
      const name = l.Company || l.Full_Name || '?';
      const rev = Number(l.Annual_Revenue) || 0;
      reply += `${i+1}. ${name}${rev ? ` — Rs. ${fmtINR(rev)}` : ''}\n`;
      if (wantsNotes) {
        const remark = (l.Business_Type || '').trim();
        const desc = (l.Description || '').trim();
        if (remark) reply += `   Remarks: ${remark.slice(0, 120)}\n`;
        if (desc) reply += `   Notes: ${desc.slice(0, 120)}\n`;
        if (!remark && !desc) reply += `   (no notes)\n`;
      }
    });
    if (salesLeads.length > 8) reply += `...+${salesLeads.length - 8} more\n`;
  }
  reply += salesCount > 0 ? `\nGreat work! Keep the momentum!` : `\nMonth abhi baaki hai — let's close some!`;
  reply += `\n— Onsite Pulse`;
}

// === PIPELINE ===
else if (intent === 'pipeline') {
  const vhpLeads = await qPage(`SELECT Full_Name, Company, Phone, Mobile, Price_PItched, Description FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = 'Very High Prospect'`);
  const hpLeads = await qPage(`SELECT Full_Name, Company, Phone, Mobile, Price_PItched, Description FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = 'High Prospect'`);
  const prospect = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sales_Stage = '1. Prospect'`);

  reply = `${displayName}'s Pipeline\n\n`;
  reply += `Very High Prospect: ${vhpLeads.length}\n`;
  if (vhpLeads.length > 0) {
    vhpLeads.forEach((l, i) => {
      reply += `  ${i+1}. ${l.Full_Name || '?'}`;
      if (l.Company) reply += ` — ${l.Company}`;
      const ph = l.Phone || l.Mobile || '';
      if (ph) reply += `\n     Ph: ${ph}`;
      if (l.Price_PItched) reply += ` | Price: ${l.Price_PItched}`;
      if (l.Description) reply += `\n     Note: ${(l.Description+'').slice(0,80)}`;
      reply += '\n';
    });
  }
  reply += `\nHigh Prospect: ${hpLeads.length}\n`;
  if (hpLeads.length > 0) {
    hpLeads.slice(0, 15).forEach((l, i) => {
      reply += `  ${i+1}. ${l.Full_Name || '?'}`;
      if (l.Company) reply += ` — ${l.Company}`;
      const ph = l.Phone || l.Mobile || '';
      if (ph) reply += `\n     Ph: ${ph}`;
      if (l.Price_PItched) reply += ` | Price: ${l.Price_PItched}`;
      reply += '\n';
    });
    if (hpLeads.length > 15) reply += `  ... +${hpLeads.length - 15} more\n`;
  }
  reply += `\nProspect: ${prospect}\n`;
  reply += `\nTotal hot leads: ${vhpLeads.length + hpLeads.length + prospect}\n`;
  reply += vhpLeads.length > 0 ? `\n${vhpLeads.length} VHP leads — follow up TODAY!` : `\nFocus on converting prospects to HP!`;
  reply += `\n— Onsite Pulse`;
}

// === FOLLOW-UPS ===
else if (intent === 'followups') {
  const overdue = await qPage(`SELECT Full_Name, Company, Lead_Task FROM Leads WHERE (${ownerFilter}) AND Lead_Task is not null AND Lead_Task < '${TODAY}T00:00:00+05:30'`);
  const todayTasks = await qPage(`SELECT Full_Name, Company, Lead_Task FROM Leads WHERE (${ownerFilter}) AND Lead_Task >= '${TODAY}T00:00:00+05:30' AND Lead_Task <= '${TODAY}T23:59:59+05:30'`);

  reply = `${displayName}'s Follow-Ups\n\n`;
  reply += `Due Today: ${todayTasks.length}\n`;
  reply += `Overdue: ${overdue.length}\n\n`;

  if (todayTasks.length > 0) {
    reply += `Today's calls:\n`;
    todayTasks.slice(0, 5).forEach((l, i) => {
      reply += `${i+1}. ${l.Company || l.Full_Name || '?'}\n`;
    });
  }
  if (overdue.length > 0) {
    reply += `\nOverdue (needs attention):\n`;
    overdue.slice(0, 3).forEach((l, i) => {
      reply += `${i+1}. ${l.Company || l.Full_Name || '?'} — was due ${(l.Lead_Task || '').slice(0, 10)}\n`;
    });
  }
  reply += `\n— Onsite Pulse`;
}

// === RANK ===
else if (intent === 'rank') {
  const allReps = await qPage(`SELECT Leads_Owner, Sale_Done_Date FROM Leads WHERE Sale_Done_Date between '${DATE_START}' and '${DATE_END}'`);

  const ranks = {};
  (allReps || []).forEach(r => {
    const owner = CRM_OWNER_MAP[r.Leads_Owner] || r.Leads_Owner;
    ranks[owner] = (ranks[owner] || 0) + 1;
  });

  const sorted = Object.entries(ranks).sort((a, b) => b[1] - a[1]);
  const myRank = sorted.findIndex(([n]) => n === repName) + 1;
  const myCount = ranks[repName] || 0;

  reply = `Team Leaderboard — ${DATE_LABEL}\n\n`;
  sorted.slice(0, 5).forEach(([name, count], i) => {
    const medal = i === 0 ? '#1' : i === 1 ? '#2' : i === 2 ? '#3' : `#${i+1}`;
    const marker = name === repName ? ' <-- YOU' : '';
    reply += `${medal} ${name}: ${count} sales${marker}\n`;
  });

  if (myRank > 5) reply += `\n...you're at #${myRank} with ${myCount} sales`;
  reply += myRank <= 3 ? `\n\nTop 3! Amazing work ${repName}!` : `\n\nLet's climb up! Every demo counts`;
  reply += `\n— Onsite Pulse`;
}

// === TARGET ===
else if (intent === 'target') {
  const mySales = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Sale_Done_Date between '${DATE_START}' and '${DATE_END}'`);
  const myDemos = await qCount(`SELECT COUNT(id) as c FROM Leads WHERE (${ownerFilter}) AND Demo_Done_Date between '${DATE_START}' and '${DATE_END}'`);
  const daysLeft = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate() - DAY_NUM;

  reply = `${displayName}'s Progress — ${DATE_LABEL}\n\n`;
  reply += `Demos Done: ${myDemos}\n`;
  reply += `Sales Closed: ${mySales}\n`;
  reply += `Days Left: ${daysLeft}\n\n`;
  reply += `Conversion Rate: ${myDemos > 0 ? Math.round(mySales / myDemos * 100) : 0}%\n`;
  reply += daysLeft > 15 ? `\nStill plenty of time — keep pushing!` : `\nFinal stretch! Close those hot leads NOW!`;
  reply += `\n— Onsite Pulse`;
}

// === LEADS ASSIGNED ===
else if (intent === 'leads_assigned') {
  // Determine date range based on dateFilter
  let assignStart, assignEnd, assignLabel;
  if (dateFilter === 'yesterday') {
    assignStart = `${YESTERDAY}T00:00:00+05:30`;
    assignEnd = `${YESTERDAY}T23:59:59+05:30`;
    assignLabel = 'Yesterday';
  } else if (dateFilter === 'this_week') {
    const weekStart = new Date(now); weekStart.setDate(now.getDate() - now.getDay() + 1); // Monday
    assignStart = `${weekStart.getFullYear()}-${pad(weekStart.getMonth()+1)}-${pad(weekStart.getDate())}T00:00:00+05:30`;
    assignEnd = `${TODAY}T23:59:59+05:30`;
    assignLabel = 'This Week';
  } else if (dateFilter === 'last_week') {
    const lwStart = new Date(now); lwStart.setDate(now.getDate() - now.getDay() - 6);
    const lwEnd = new Date(now); lwEnd.setDate(now.getDate() - now.getDay());
    assignStart = `${lwStart.getFullYear()}-${pad(lwStart.getMonth()+1)}-${pad(lwStart.getDate())}T00:00:00+05:30`;
    assignEnd = `${lwEnd.getFullYear()}-${pad(lwEnd.getMonth()+1)}-${pad(lwEnd.getDate())}T23:59:59+05:30`;
    assignLabel = 'Last Week';
  } else {
    // Default: today
    assignStart = `${TODAY}T00:00:00+05:30`;
    assignEnd = `${TODAY}T23:59:59+05:30`;
    assignLabel = 'Today';
  }

  const assignedLeads = await qPage(`SELECT Full_Name, Company, Phone, Mobile, Lead_Source, Lead_Assigned_Time FROM Leads WHERE (${ownerFilter}) AND Lead_Assigned_Time between '${assignStart}' and '${assignEnd}' ORDER BY Lead_Assigned_Time DESC`);
  const count = assignedLeads.length;

  reply = `${displayName}'s Leads Assigned — ${assignLabel}\n\n`;
  reply += `Total: ${count} leads\n\n`;

  if (count > 0) {
    assignedLeads.slice(0, 15).forEach((l, i) => {
      const name = l.Full_Name || '?';
      const comp = l.Company ? ` — ${l.Company}` : '';
      const ph = l.Phone || l.Mobile || '';
      const src = l.Lead_Source || '';
      const time = (l.Lead_Assigned_Time || '').slice(11, 16);
      reply += `${i+1}. ${name}${comp}\n`;
      if (ph) reply += `   Ph: ${ph}\n`;
      if (src) reply += `   Source: ${src}\n`;
      if (time) reply += `   Time: ${time}\n`;
    });
    if (count > 15) reply += `\n...+${count - 15} more\n`;

    // Source breakdown
    const srcMap = {};
    assignedLeads.forEach(l => { const s = l.Lead_Source || 'Unknown'; srcMap[s] = (srcMap[s] || 0) + 1; });
    reply += `\nBy Source:\n`;
    Object.entries(srcMap).sort((a,b) => b[1] - a[1]).forEach(([s, c]) => {
      reply += `  ${s}: ${c}\n`;
    });
  } else {
    reply += `No leads assigned ${assignLabel.toLowerCase()}.\n`;
  }
  reply += `\n— Onsite Pulse`;
}

// === CUSTOMER REFERENCE (premium customer lookup) ===
else if (intent === 'customer_reference') {
  const CAT_NAMES = {C:'Construction', I:'Interior', M:'MEP', A:'Consulting', G:'General'};
  const REG_NAMES = {IN:'India', ME:'Middle East', AF:'Africa', SE:'South East Asia'};
  const ml = msgLower;

  // Detect category
  let fCat = null;
  if (/\b(construct|infra|builder|civil|road|bridge|housing)\b/.test(ml)) fCat = 'C';
  else if (/\b(interior|decor|furnish|design|kitchen|modular|wood)\b/.test(ml)) fCat = 'I';
  else if (/\b(mep|electric|plumb|hvac|fire|elevator|lift)\b/.test(ml)) fCat = 'M';
  else if (/\b(architect|consult|pmc)\b/.test(ml)) fCat = 'A';

  // Detect region
  let fReg = null;
  if (/\b(middle east|uae|dubai|oman|qatar|saudi|kuwait|bahrain)\b/.test(ml)) fReg = 'ME';
  else if (/\b(africa|nigeria|kenya|south africa)\b/.test(ml)) fReg = 'AF';
  else if (/\b(south east|indonesia|bali|philipp|malaysia)\b/.test(ml)) fReg = 'SE';

  // Detect state — alias map handles typos, abbreviations, alternate spellings
  const STATE_ALIAS = {
    'rajasthan':'Rajasthan','rajashthan':'Rajasthan','rajastan':'Rajasthan','rajstan':'Rajasthan',
    'maharashtra':'Maharashtra','maharastra':'Maharashtra','maha':'Maharashtra',
    'karnataka':'Karnataka','karnatak':'Karnataka',
    'tamil nadu':'Tamil Nadu','tamilnadu':'Tamil Nadu','tn':'Tamil Nadu',
    'telangana':'Telangana','telengana':'Telangana','hyderabad':'Telangana',
    'andhra pradesh':'Andhra Pradesh','andhra':'Andhra Pradesh','ap':'Andhra Pradesh',
    'uttar pradesh':'Uttar Pradesh','up':'Uttar Pradesh','uttarpradesh':'Uttar Pradesh',
    'madhya pradesh':'Madhya Pradesh','mp':'Madhya Pradesh',
    'gujarat':'Gujarat','gujrat':'Gujarat','gj':'Gujarat',
    'chhattisgarh':'Chhattisgarh','chattisgarh':'Chhattisgarh','cg':'Chhattisgarh','chhatisgarh':'Chhattisgarh',
    'kerala':'Kerala','kl':'Kerala',
    'delhi':'Delhi',
    'punjab':'Punjab','pb':'Punjab',
    'haryana':'Haryana','hr':'Haryana',
    'west bengal':'West Bengal','wb':'West Bengal','bengal':'West Bengal',
    'bihar':'Bihar',
    'jharkhand':'Jharkhand','jh':'Jharkhand',
    'odisha':'Odisha','odisa':'Odisha','orissa':'Odisha',
    'assam':'Assam',
    'goa':'Goa',
    'uttarakhand':'Uttarakhand','uk':'Uttarakhand',
    'himachal pradesh':'Himachal Pradesh','himachal':'Himachal Pradesh','hp':'Himachal Pradesh',
    'jammu':'Jammu & Kashmir','kashmir':'Jammu & Kashmir','jk':'Jammu & Kashmir',
    'chandigarh':'Chandigarh',
    'tripura':'Tripura',
    'manipur':'Manipur',
    'meghalaya':'Meghalaya',
    'mizoram':'Mizoram',
    'uae':'UAE','dubai':'UAE',
    'saudi':'Saudi Arabia','saudi arabia':'Saudi Arabia',
    'oman':'Oman','qatar':'Qatar','kuwait':'Kuwait',
    'indonesia':'Indonesia','indonasia':'Indonasia',
  };
  let fState = null;
  // Try longest alias first (multi-word like "tamil nadu" before "tamil")
  const sortedAliases = Object.keys(STATE_ALIAS).sort((a,b) => b.length - a.length);
  for (const alias of sortedAliases) {
    if (ml.includes(alias)) { fState = STATE_ALIAS[alias]; break; }
  }
  // Also match exact state names from data
  if (!fState) {
    const allStates = [...new Set(PCUST.map(c => c[2]))];
    for (const s of allStates) {
      if (ml.includes(s.toLowerCase())) { fState = s; break; }
    }
  }

  // Detect city (match against data)
  let fCity = null;
  if (!fState) {
    const allCities = [...new Set(PCUST.map(c => c[1]).filter(c => c && c.length > 2))];
    for (const c of allCities) {
      if (ml.includes(c.toLowerCase())) { fCity = c; break; }
    }
  }

  // Filter
  let results = PCUST;
  // Match state with fuzzy — "Rajasthan" also matches "Rajashthan", "Odisha" matches "Odisa"
  if (fState) {
    const fsl = fState.toLowerCase();
    results = results.filter(c => c[2] === fState || c[2].toLowerCase().startsWith(fsl.slice(0,5)));
  }
  if (fCity) results = results.filter(c => c[1].toLowerCase().includes(fCity.toLowerCase()));
  if (fCat) results = results.filter(c => c[4] === fCat);
  if (fReg) results = results.filter(c => c[3] === fReg);

  // If "more" — use saved filters from history
  if (_refOffset > 0 && !fState && !fCity && !fCat && !fReg) {
    fState = _refState; fCity = _refCity; fCat = _refCat; fReg = _refReg;
    results = PCUST;
    if (fState) { const fsl = fState.toLowerCase(); results = results.filter(c => c[2] === fState || c[2].toLowerCase().startsWith(fsl.slice(0,5))); }
    if (fCity) results = results.filter(c => c[1].toLowerCase().includes(fCity.toLowerCase()));
    if (fCat) results = results.filter(c => c[4] === fCat);
    if (fReg) results = results.filter(c => c[3] === fReg);
  }
  _refState = fState; _refCity = fCity; _refCat = fCat; _refReg = fReg;

  results = [...results].sort((a,b) => b[5] - a[5]);
  const top = results.slice(_refOffset, _refOffset + 5);

  let label = fState || fCity || (fReg ? REG_NAMES[fReg] : null) || 'All';
  if (fCat) label += ' \u2014 ' + CAT_NAMES[fCat];
  const pageNum = _refOffset > 0 ? ' (Page ' + (Math.floor(_refOffset/5)+1) + ')' : '';

  if (top.length === 0) {
    reply = _refOffset > 0
      ? 'No more customers for "' + label + '". Showing all ' + results.length + ' done.\n\n\u2014 Onsite Pulse'
      : 'No premium customers found for "' + label + '".\n\nTry: "premium customers from Maharashtra" or "interior companies Gujarat"\n\n\u2014 Onsite Pulse';
  } else {
    reply = '*Premium Customers \u2014 ' + label + '*' + pageNum + '\n\n';
    top.forEach((c, i) => {
      const [comp, city, st, reg, cat, amt, renew, age] = c;
      const cityStr = city ? ' (' + city + ')' : '';
      const status = renew ? '\ud83d\udd04 Renewal' : '\ud83c\udd95 Fresh';
      const ageStr = age >= 24 ? Math.floor(age/12) + 'yr' : age >= 1 ? age + 'mo' : 'New';
      const amtStr = amt >= 100000 ? (amt/100000).toFixed(1) + 'L' : (amt/1000).toFixed(0) + 'K';
      reply += (_refOffset + i + 1) + '. *' + comp + '*' + cityStr + '\n';
      reply += '   ' + (fCat ? CAT_NAMES[cat] + ' | ' : '') + '\u20b9' + amtStr + ' | ' + status + ' | ' + ageStr + '\n\n';
    });
    reply += '--- _Copy-paste for client_ ---\n';
    reply += '*Paid Users \u2014 ' + label + '*\n';
    if (fCat) {
      const byCat = {};
      top.forEach(c => { const cn = CAT_NAMES[c[4]]; if (!byCat[cn]) byCat[cn]=[]; byCat[cn].push(c[0]); });
      const catKeys = Object.keys(byCat);
      for (const cat of catKeys) {
        if (catKeys.length > 1) reply += '_' + cat + '_\n';
        byCat[cat].forEach(name => { reply += '\u2022 ' + name + '\n'; });
      }
    } else {
      top.forEach(c => { reply += '\u2022 ' + c[0] + '\n'; });
    }
    const remaining = results.length - _refOffset - top.length;
    reply += '\n_Showing ' + (_refOffset+1) + '-' + (_refOffset+top.length) + ' of ' + results.length + '_';
    if (remaining > 0) reply += '\n_Say "more" for next ' + Math.min(5, remaining) + '_';
    reply += '\n\u2014 Onsite Pulse';
  }
}

// === NOTES (standalone — recent leads with remarks/notes) ===
else if (intent === 'notes') {
  const notesLeads = await qPage(`SELECT Full_Name, Company, Business_Type, Description, Modified_Time FROM Leads WHERE (${ownerFilter}) ORDER BY Modified_Time DESC`);

  reply = `${displayName}'s Recent Notes\n\n`;
  if (notesLeads.length > 0) {
    let shown = 0;
    for (const l of notesLeads) {
      if (shown >= 10) break;
      const remark = (l.Business_Type || '').trim();
      const desc = (l.Description || '').trim();
      if (!remark && !desc) continue;
      const name = l.Company || l.Full_Name || '?';
      const date = (l.Modified_Time || '').slice(0, 10);
      reply += `${shown+1}. ${name} (${date})\n`;
      if (remark) reply += `   Remarks: ${remark.slice(0, 150)}\n`;
      if (desc) reply += `   Notes: ${desc.slice(0, 150)}\n`;
      reply += `\n`;
      shown++;
    }
    if (shown === 0) reply += `No notes found for your leads.\n`;
    else if (notesLeads.length > 10) reply += `...+${notesLeads.length - 10} more leads with notes\n`;
  } else {
    reply += `No notes found. Add remarks in CRM for better tracking!\n`;
  }
  reply += `Tip: "demos with notes" or "sales with notes" for specific views\n— Onsite Pulse`;
}

// === LEAD SEARCH (by phone, name, or company) ===
else if (intent === 'lead_search') {
  let searchFilter = '';
  let searchLabel = '';
  if (searchPhone) {
    const ph = searchPhone.replace(/[^0-9]/g, '');
    // Try partial match — last 10 digits
    const ph10 = ph.slice(-10);
    searchFilter = `Phone like '%${ph10}%' OR Mobile like '%${ph10}%'`;
    searchLabel = `phone ${ph10}`;
  } else if (searchCompany || searchName) {
    // Use the first significant keyword (2+ words → first 2, else first word)
    const raw = (searchCompany || searchName || '').replace(/'/g, "\\'");
    const words = raw.split(/\s+/).filter(w => w.length > 1);
    // Search both Company AND Full_Name with first keyword for broader match
    const kw = words[0] || raw;
    searchFilter = `Company like '%${kw}%' OR Full_Name like '%${kw}%'`;
    searchLabel = searchCompany ? `company "${searchCompany}"` : `name "${searchName}"`;
  } else {
    reply = `Please provide a phone number, lead name, or company name to search.\n\nExamples:\n"find lead 9876543210"\n"search company ABC Builders"\n"lead named Rahul"\n— Onsite Pulse`;
  }

  if (searchFilter && !reply) {
    // Search without scope in COQL (like + complex OR breaks Zoho), filter by role in JS
    const rawResults = await qPage(`SELECT id, Full_Name, Company, Phone, Mobile, Leads_Owner, Sales_Stage, Lead_Status, Annual_Revenue, Business_Type, Description, Demo_Done_Date, Sale_Done_Date FROM Leads WHERE (${searchFilter}) ORDER BY Modified_Time DESC`);

    // Build allowed owner names for this user's role
    let results = rawResults;
    if (myRole !== 'admin') {
      const allowed = new Set();
      const names = myRole === 'team_lead' ? [repName, ...(LEAD_ACCESS[repName] || [])] : [repName];
      names.forEach(n => {
        allowed.add(n);
        Object.entries(CRM_OWNER_MAP).forEach(([k, v]) => { if (v === n) allowed.add(k); });
      });
      results = rawResults.filter(l => allowed.has(l.Leads_Owner));
    }

    reply = `Search: ${searchLabel}\n\n`;
    if (results.length === 0) {
      reply += `No leads found. Try a different search term.`;
    } else {
      reply += `Found ${results.length} lead${results.length > 1 ? 's' : ''}:\n\n`;
      // For top 3 results, also fetch Zoho Notes (related list)
      const topResults = results.slice(0, 5);
      for (let i = 0; i < topResults.length; i++) {
        const l = topResults[i];
        const name = l.Full_Name || '?';
        const comp = l.Company ? ` (${l.Company})` : '';
        const phone = l.Phone || l.Mobile || '';
        const owner = CRM_OWNER_MAP[l.Leads_Owner] || l.Leads_Owner || '';
        const stage = l.Sales_Stage || l.Lead_Status || '';
        const rev = Number(l.Annual_Revenue) || 0;
        reply += `${i+1}. ${name}${comp}\n`;
        if (phone) reply += `   Phone: ${phone}\n`;
        if (owner) reply += `   Owner: ${owner}\n`;
        if (stage) reply += `   Stage: ${stage}\n`;
        if (rev) reply += `   Revenue: Rs. ${fmtINR(rev)}\n`;
        if (l.Demo_Done_Date) reply += `   Demo: ${(l.Demo_Done_Date || '').slice(0, 10)}\n`;
        if (l.Sale_Done_Date) reply += `   Sale: ${(l.Sale_Done_Date || '').slice(0, 10)}\n`;
        const remark = (l.Business_Type || '').trim();
        const desc = (l.Description || '').trim();
        if (remark) reply += `   Remarks: ${remark.slice(0, 150)}\n`;
        if (desc) reply += `   Description: ${desc.slice(0, 150)}\n`;
        // Fetch Zoho Notes (related list) for this lead
        if (l.id && i < 3) {
          try {
            const t = await getToken();
            const notesResp = await http({method:'GET',
              url:`https://www.zohoapis.in/crm/v7/Leads/${l.id}/Notes?fields=Note_Content,Note_Title,Created_Time,Modified_Time`,
              headers:{Authorization:`Zoho-oauthtoken ${t}`}});
            const notesData = typeof notesResp === 'string' ? JSON.parse(notesResp) : notesResp;
            if (notesData?.data?.length > 0) {
              reply += `   CRM Notes:\n`;
              notesData.data.slice(0, 3).forEach(n => {
                // Strip HTML tags from Note_Content
                let noteText = (n.Note_Content || n.Note_Title || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
                const noteDate = (n.Modified_Time || n.Created_Time || '').slice(0, 10);
                if (noteText) reply += `   - ${noteDate}: ${noteText.slice(0, 250)}\n`;
              });
            }
          } catch(e) { /* notes API failed, skip */ }
        }
        reply += `\n`;
      }
      if (results.length > 5) reply += `...+${results.length - 5} more\n`;
    }
    reply += `\n— Onsite Pulse`;
  }
}

// === SALES ASSISTANT (AI-powered with full Onsite knowledge) ===
else if (intent === 'assistant') {
  // Build lead context from memory for personalized answers
  let leadInfo = '';
  const lastCtx = chatHistory.length > 0 ? chatHistory[chatHistory.length - 1]?.lead_context : null;
  if (lastCtx?.lead_name) leadInfo = `\nThe rep was recently discussing lead: ${lastCtx.lead_name}${lastCtx.lead_phone ? ` (${lastCtx.lead_phone})` : ''}. Use this context if relevant.`;

  const ONSITE_KNOWLEDGE = `You are the Onsite Pulse Sales Assistant for Onsite Teams — a construction management SaaS.

ABOUT ONSITE:
- Construction Management Software & ERP (SaaS) — Project, Material, Labor, Finance, Procurement, Quality, Design modules
- 10,000+ companies, ISO certified, mobile-first, implementation in 1-2 weeks
- Website: onsiteteams.com | Founded 2021 | Office: Noida, UP

PRICING (National — INR, +18% GST):
- Business: Rs.12,000/user/year — Payments, Files, Attendance, Salary, CRM, Inventory, Tasks, Issues, Subcon
- Business+: Rs.15,000/user/year — All Business + Design Mgmt, BOQ/RA Bills, Budget Control, Warehouse, RFQ, POs, Assets, Payroll, Inspection, Multi-Level Approval
- Enterprise: Rs.12,00,000 lump sum — Unlimited Users, GPS, Custom Dashboards, Tally/Zoho Integration, Vendor/Client Portals, White Label
- Add-ons: GPS Attendance 20K, Additional Company 20K, Tally Integration 20K+5K AMC, Additional Users 5K/user/year

PRICING (International — USD, no GST):
- Business: $200/user/year | Business+: $250/user/year | Enterprise: $15,000 lump sum
- White Label: Web $3,600, Android $4,200, iOS $4,800
- Add-ons: GPS $300, Additional Company $300, Additional Users $60/user/year

KEY USPs:
- 10-20x cheaper than Procore ($200/user/year vs $2,388-4,500)
- Mobile-first (site workers use phones, Hindi support)
- 1-2 week implementation (vs months for traditional ERP)
- Up to 7% cost savings on projects
- ISO certified, RERA & GST compliant

COMPETITORS:
India: Powerplay (700K users, budget), NYGGS (AI/IoT, infra), StrategicERP (flexible), RDash (9K projects)
Global: Procore ($199-375/user/mo), Buildertrend ($299-499/mo), PlanGrid ($39-199/user/mo), Fieldwire, Oracle Aconex

OBJECTION HANDLING:
- "Too expensive" → ROI: 7% savings on 10Cr project = 70L saved. One material theft > annual subscription
- "My team can't use it" → Mobile-first, Hindi, on-site training. Simpler than WhatsApp groups
- "We use Excel" → Show time saved, error reduction, real-time visibility across sites
- "Data security" → ISO certified, enterprise cloud, data ownership guarantee
- "Not the right time" → Cost overruns happening NOW. Every month without tracking = money lost
- "Already using competitor" → Integration possible, feature comparison, lower cost

SALES APPROACH:
- Builders are phone-first, relationship-driven — calls > emails
- Lead with ROI numbers, not features: "save 2 hours daily" beats "AI-powered"
- Short 15-20 min demos beat hour-long presentations
- Free trial / pilot on one site reduces risk
- Construction buyers are first-time software buyers — educate WHY before WHICH
- WhatsApp follow-ups work better than email in construction

BUYER PAIN POINTS:
1. Manual processes (57%) — paper DPRs, Excel, WhatsApp chaos
2. Cost overruns (10-30%) — no budget visibility, material wastage
3. Multi-site chaos — no single source of truth
4. Cash flow blindness — manual RA billing
5. Compliance headaches — GST, RERA, labor laws

EMAIL/MESSAGE TEMPLATES STYLE:
- Keep it short (3-4 lines max for WhatsApp, 5-6 for email)
- Start with pain point or value, not features
- Use INR for Indian clients, USD for international
- Include specific ROI numbers
- End with clear CTA (call/demo/trial)
- Tone: professional but practical, not salesy

CONSTRUCTION TERMS:
DPR = Daily Progress Report, RA Bills = Running Account Bills, BOQ = Bill of Quantities, RFQ = Request for Quotation, PO = Purchase Order, AMC = Annual Maintenance Contract
${leadInfo}
${conversationContext}`;

  try {
    const assistResp = await http({
      method: 'POST',
      url: 'https://openrouter.ai/api/v1/chat/completions',
      headers: { 'Authorization': `Bearer ${OR_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'anthropic/claude-haiku-4.5',
        max_tokens: 800,
        temperature: 0.3,
        messages: [
          { role: 'system', content: ONSITE_KNOWLEDGE },
          { role: 'user', content: `I am ${repName}, a sales rep at Onsite Teams. ${msg}` }
        ]
      })
    });
    const aParsed = typeof assistResp === 'string' ? JSON.parse(assistResp) : assistResp;
    reply = (aParsed?.choices?.[0]?.message?.content || '').trim();
    if (!reply) reply = 'Sorry, could not generate a response. Try rephrasing your question.';
    reply += `\n\n— Onsite Pulse Assistant`;
  } catch(e) {
    reply = `Sorry ${repName}, assistant is temporarily unavailable. Try again in a moment.\n— Onsite Pulse`;
  }
}

// === GENERAL CHAT (AI-powered reply) ===
else {
  if (aiReply) {
    reply = aiReply + `\n\nNeed help? Try "write a follow-up email", "our pricing", "how to handle objection", or say "help".\n— Onsite Pulse`;
  } else {
    const funReplies = [
      `Hey ${repName}! Samajh nahi aaya — Try "my demos", "our pricing", "write a follow-up email", or "help"!`,
      `${repName}, I can help with sales data AND sales coaching! Type "help" for everything I can do`,
      `Hmm interesting ${repName}... try asking about pricing, pipeline, or "help me close this deal"!`,
      `${repName}, mere paas data bhi hai aur sales tips bhi! Type "help" for options`,
    ];
    reply = funReplies[Math.floor(Math.random() * funReplies.length)];
  }
}

// === SEND TO WHATSAPP (auto for useful intents) ===
// Look up rep's phone number
const ALL_PHONES = {...MGR, ...REPS, ...PRE_SALES};
const repPhone = ALL_PHONES[repName];
let sentToWA = false;

// Auto-send to WhatsApp for: assistant, followups, lead_search, demos/sales with notes, or any long reply
const waIntents = ['assistant', 'followups', 'lead_search'];
const shouldSendWA = repPhone && reply && intent !== 'greeting' && intent !== 'help' && intent !== 'chat' && (
  waIntents.includes(intent) ||
  (wantsNotes && ['demos', 'sales', 'notes'].includes(intent)) ||
  reply.length > 500
);

if (shouldSendWA) {
  try {
    // Clean markdown bold/italic for WhatsApp (** → *, keep single *)
    const waMsg = `Pulse Chat — ${repName}\nQ: ${msg}\n\n${reply.replace(/\*\*/g, '*')}`;
    await wa(repPhone, waMsg.slice(0, 4096), repName);
    sentToWA = true;
    reply += `\n\nSent to your WhatsApp`;
  } catch(e) { /* WA send failed — non-critical */ }
}

// === STORE TO MEMORY ===
// Build lead context from search results if applicable
let leadCtx = {};
if (intent === 'lead_search' && searchPhone) leadCtx.lead_phone = searchPhone;
if (intent === 'lead_search' && (searchName || searchCompany)) leadCtx.lead_name = searchName || searchCompany;
if (intent === 'customer_reference') { leadCtx.ref_state = _refState; leadCtx.ref_city = _refCity; leadCtx.ref_cat = _refCat; leadCtx.ref_reg = _refReg; leadCtx.ref_offset = _refOffset || 0; }
// Carry forward lead context from last message if user is referencing "same lead"
if (chatHistory.length > 0 && !leadCtx.lead_name && !leadCtx.lead_phone) {
  const lastCtx = chatHistory[chatHistory.length - 1]?.lead_context;
  if (lastCtx?.lead_name || lastCtx?.lead_phone) {
    if (/\b(same|that|this|uska|iska|wahi|us|is)\b/i.test(msg)) leadCtx = lastCtx;
  }
}
// Store conversation (non-blocking)
sbStore(repName, msg, reply, intent, leadCtx).catch(() => {});

return [{ json: { reply, status: 'ok', intent, repName, sentToWA } }];
"""

# === AUTO 10: EMAIL PIPELINE (triggered by Zoho status changes) ===
# Code node polls Zoho for recently modified leads, dedupes against Supabase,
# renders branded HTML emails, and outputs items for Gmail Send node.
AUTO_10_JS = r"""
// === AUTO 10: EMAIL PIPELINE ===
const SB_URL = '%SUPABASE_URL%';
const SB_KEY = '%SUPABASE_KEY%';
const SB_HEADERS = {'apikey':SB_KEY,'Authorization':`Bearer ${SB_KEY}`,'Content-Type':'application/json','Prefer':'return=minimal'};

// === REP EMAIL ADDRESSES ===
const REP_EMAILS = {
  'Dhruv': 'dhruv.tomar@onsiteteams.com',
  'Bhavya': 'bhavya.j@onsiteteams.com',
  'Anjali': 'anjali.b@onsiteteams.com',
  'Sunil': 'sunil.kumar@onsiteteams.com',
  'Amit U': 'amit.u@onsiteteams.com',
  'Mohan': 'mohan.c@onsiteteams.com',
  'Gayatri': 'gayatri.surlkar@onsiteteams.com',
  'Shailendra': 'shailendra.g@onsiteteams.com',
  'Amit Kumar': 'amit.k@onsiteteams.com',
  'Hitangi': 'hitangi.a@onsiteteams.com',
  'Shruti': 'shruti.a@onsiteteams.com',
  'Ravi': 'ravi.gupta@onsiteteams.com',
  'Arthi': 'aparthivarsha@onsiteteams.com',
  'Kiran': 'k.kiran@onsiteteams.com',
  'Yogyata': 'yogyata.airi@onsiteteams.com'
};

const TANIYA_EMAIL = 'taniya.malhotra@onsiteteams.com';

const DEMO_LINKS = {
  'Anjali': 'https://meet.google.com/hmc-pzdo-jxx',
  'Gayatri': 'https://meet.google.com/gir-uyss-veq',
  'Bhavya': 'https://meet.google.com/vfk-iust-xrj',
  'Shailendra': 'https://meet.google.com/rkm-kphu-tta',
  'Hitangi': 'https://meet.google.com/bpg-wqbb-fbz',
  'Mohan': 'https://meet.google.com/pzr-egje-ffc',
  'Amit U': 'https://meet.google.com/ezu-osvu-zsf',
  'Amit Kumar': 'https://meet.google.com/qsg-gcwi-qrq',
  'Sunil': 'https://meet.google.com/hay-bcrj-uea',
};

// Status → template mapping
const STATUS_TO_TEMPLATE = {
  '2. Priority Leads': 'welcome',
  '3. Qualified': 'welcome',
  '6. Demo booked': 'demo_booked',
  'NATC': 'natc',
  'User not attend session': 'user_not_attend',
  '7. Demo done': 'demo_done',
  '10. Not Interested (Not Potential)': 'not_interested',
  '10. Not Interested': 'not_interested',
  '12. Subscribed': 'onboarding_welcome'
};

// Sales Stage → template (checked if no status match)
const STAGE_TO_TEMPLATE = {
  'Prospect': 'prospect_nurture',
  'High Prospect': 'vhp_hp_followup',
  'Very High Prospect': 'vhp_hp_followup'
};

// === SUPABASE DEDUP ===
async function sbCheckSent(leadId, templateKey, leadStatus) {
  try {
    const resp = await http({method:'GET',
      url:`${SB_URL}/rest/v1/email_sent_log?lead_id=eq.${leadId}&template_key=eq.${encodeURIComponent(templateKey)}&lead_status=eq.${encodeURIComponent(leadStatus)}&select=id&limit=1`,
      headers:{...SB_HEADERS, 'Prefer':''}});
    const data = typeof resp === 'string' ? JSON.parse(resp) : resp;
    return Array.isArray(data) && data.length > 0;
  } catch(e) { return false; }
}

async function sbLogSent(obj) {
  try {
    await http({method:'POST', url:`${SB_URL}/rest/v1/email_sent_log`,
      headers:SB_HEADERS,
      body:JSON.stringify(obj)});
  } catch(e) { /* non-critical */ }
}

// === SENDER LOGIC ===
function getSender(lead, templateKey) {
  if (templateKey === 'welcome' || templateKey === 'onboarding_welcome') {
    return { name: 'Taniya Malhotra - Onsite Teams', replyTo: TANIYA_EMAIL };
  }
  const ownerRaw = String(lead.Leads_Owner || lead.Deal_Owner || '').trim();
  const ownerShort = CRM_OWNER_MAP[ownerRaw] || ownerRaw;
  const repEmail = REP_EMAILS[ownerShort];
  if (repEmail) {
    return { name: `${ownerShort} - Onsite Teams`, replyTo: repEmail };
  }
  return { name: 'Onsite Teams', replyTo: TANIYA_EMAIL };
}

// === HTML EMAIL WRAPPER ===
function emailWrap(headline, bodyHtml, ctaUrl, ctaText, senderName, senderEmail) {
  const cta = ctaUrl ? `<div style="text-align:center;margin:24px 0;"><a href="${ctaUrl}" style="display:inline-block;background:#c73e5a;color:#ffffff;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:600;font-size:15px;">${ctaText || 'Learn More'}</a></div>` : '';
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head><body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;background:#f1f5f9;padding:20px 0;">
  <div style="background:linear-gradient(135deg,#1a0b50 0%,#2d1670 100%);padding:28px 24px;text-align:center;border-radius:8px 8px 0 0;">
    <img src="https://www.onsiteteams.com/_next/image?url=%2Fimages%2Flogo-white.webp&w=384&q=75" alt="Onsite Teams" height="36" style="height:36px;">
  </div>
  <div style="background:#ffffff;padding:32px 28px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <h2 style="color:#1a0b50;margin:0 0 16px;font-size:20px;">${headline}</h2>
    <div style="color:#334155;line-height:1.7;font-size:15px;">${bodyHtml}</div>
    ${cta}
  </div>
  <div style="padding:20px 24px;text-align:center;font-size:12px;color:#94a3b8;">
    <p style="margin:4px 0;">${senderName || 'Onsite Teams'} ${senderEmail ? '| ' + senderEmail : ''}</p>
    <p style="margin:4px 0;">Onsite Teams — Construction Management Software</p>
    <p style="margin:4px 0;"><a href="https://www.onsiteteams.com" style="color:#6366f1;text-decoration:none;">onsiteteams.com</a></p>
  </div>
</div></body></html>`;
}

// === 11 EMAIL TEMPLATES ===
function renderTemplate(key, lead, sender) {
  const firstName = (lead.Full_Name || 'there').split(' ')[0];
  const company = lead.Company || 'your company';
  const ownerShort = CRM_OWNER_MAP[String(lead.Leads_Owner || '').trim()] || 'Our team';
  const repEmail = REP_EMAILS[ownerShort] || TANIYA_EMAIL;
  const demoLink = DEMO_LINKS[ownerShort] || '';

  switch(key) {
    case 'welcome':
      return {
        subject: `Welcome to Onsite Teams — Let's Build Smarter, ${firstName}`,
        html: emailWrap(
          `Welcome, ${firstName}!`,
          `<p>Hi ${firstName},</p>
          <p>Thank you for showing interest in <strong>Onsite Teams</strong> — India's leading construction management software trusted by 10,000+ companies.</p>
          <p>Here's what Onsite can do for ${company}:</p>
          <ul style="padding-left:20px;">
            <li><strong>Save up to 7%</strong> on project costs with real-time tracking</li>
            <li><strong>Go live in 1-2 weeks</strong> — not months like traditional ERPs</li>
            <li><strong>Mobile-first design</strong> — your site team can use it from day one</li>
          </ul>
          <p>Your dedicated point of contact, <strong>${ownerShort}</strong>, will reach out shortly to understand your needs and schedule a quick demo.</p>
          <p>In the meantime, feel free to explore our platform!</p>`,
          'https://www.onsiteteams.com', 'Explore Onsite Teams',
          sender.name, sender.replyTo
        )
      };

    case 'demo_booked':
      return {
        subject: `Your Onsite Teams Demo is Confirmed!`,
        html: emailWrap(
          `Demo Confirmed! 🎉`,
          `<p>Hi ${firstName},</p>
          <p>Great news — your demo with <strong>${ownerShort}</strong> has been scheduled!</p>
          ${demoLink ? `<p><strong>Join Link:</strong> <a href="${demoLink}" style="color:#6366f1;">${demoLink}</a></p>` : ''}
          <p style="background:#f0f9ff;padding:16px;border-radius:6px;border-left:4px solid #1a0b50;">
            <strong>What to expect:</strong><br>
            • A 15-20 minute walkthrough of Onsite Teams<br>
            • Customized to ${company}'s needs<br>
            • Live Q&A with our product expert
          </p>
          <p>If you need to reschedule, just reply to this email or call ${ownerShort} directly.</p>`,
          demoLink, 'Join Demo',
          sender.name, sender.replyTo
        )
      };

    case 'demo_done':
      return {
        subject: `Thanks for the Demo — Here's What's Next, ${firstName}`,
        html: emailWrap(
          `Thanks for Your Time, ${firstName}!`,
          `<p>Hi ${firstName},</p>
          <p>It was great showing you how Onsite Teams can help ${company}. Here's a quick recap:</p>
          <ul style="padding-left:20px;">
            <li><strong>Project Management</strong> — DPR automation, real-time progress tracking</li>
            <li><strong>Material & Inventory</strong> — Reduce wastage, track every kg</li>
            <li><strong>Workforce</strong> — GPS attendance, automated salary processing</li>
            <li><strong>Financial</strong> — RA bills, budgeting, GST-compliant invoicing</li>
          </ul>
          <p>Companies like yours typically see <strong>7% cost savings</strong> within the first 3 months.</p>
          <p><strong>Next steps:</strong></p>
          <ol style="padding-left:20px;">
            <li>I'll send you a customized quotation</li>
            <li>We can set up a pilot on one of your projects</li>
            <li>Go live in just 1-2 weeks!</li>
          </ol>
          <p>Have questions? Just reply to this email — I'm here to help.</p>`,
          'https://www.onsiteteams.com/onsite-pricing', 'View Pricing',
          sender.name, sender.replyTo
        )
      };

    case 'natc':
      return {
        subject: `We Tried Reaching You — Onsite Teams`,
        html: emailWrap(
          `We Tried Calling You, ${firstName}`,
          `<p>Hi ${firstName},</p>
          <p>I tried reaching you by phone but couldn't connect. No worries — I understand you're busy managing projects!</p>
          <p>I wanted to discuss how <strong>Onsite Teams</strong> can help ${company}:</p>
          <ul style="padding-left:20px;">
            <li>Reduce cost overruns by up to <strong>7%</strong></li>
            <li>Replace Excel + WhatsApp chaos with one platform</li>
            <li>Get live visibility across all your sites</li>
          </ul>
          <p>Would any of these times work for a quick 15-minute call?</p>
          <p style="background:#fef3c7;padding:16px;border-radius:6px;border-left:4px solid #f59e0b;">
            Simply reply with a convenient time, and I'll call you!
          </p>`,
          null, null,
          sender.name, sender.replyTo
        )
      };

    case 'user_not_attend':
      return {
        subject: `We Missed You — Let's Reschedule Your Demo`,
        html: emailWrap(
          `We Missed You, ${firstName}!`,
          `<p>Hi ${firstName},</p>
          <p>It looks like we missed you at the scheduled demo. No problem at all — we know construction schedules can be unpredictable!</p>
          <p>I'd love to reschedule at a time that works better for you. The demo takes just <strong>15-20 minutes</strong> and could save ${company} lakhs every year.</p>
          ${demoLink ? `<p>You can book directly using this link:</p>` : `<p>Just reply with your preferred time and I'll set it up.</p>`}`,
          demoLink || null, demoLink ? 'Reschedule Demo' : null,
          sender.name, sender.replyTo
        )
      };

    case 'prospect_nurture':
      return {
        subject: `Construction Companies Are Saving 7% on Costs — Here's How`,
        html: emailWrap(
          `Are Cost Overruns Eating Your Margins, ${firstName}?`,
          `<p>Hi ${firstName},</p>
          <p>Did you know that <strong>10-30% cost overruns</strong> are the #1 problem in Indian construction? Most companies lose money they don't even know about — material wastage, labor fraud, delayed billing.</p>
          <p><strong>Here's what Onsite Teams customers report:</strong></p>
          <ul style="padding-left:20px;">
            <li>📉 <strong>7% average cost reduction</strong> in the first quarter</li>
            <li>⏱️ <strong>15+ hours saved per week</strong> on reporting and coordination</li>
            <li>📱 <strong>Real-time visibility</strong> across all project sites</li>
          </ul>
          <p>Would you like to see how this could work for ${company}? I can arrange a quick demo or send you a case study.</p>`,
          'https://www.onsiteteams.com', 'See How It Works',
          sender.name, sender.replyTo
        )
      };

    case 'vhp_hp_followup':
      return {
        subject: `Quick Question About Your Decision, ${firstName}`,
        html: emailWrap(
          `Following Up, ${firstName}`,
          `<p>Hi ${firstName},</p>
          <p>I wanted to check in — after our demo, is there anything holding you back from getting started with Onsite Teams?</p>
          <p>I ask because the sooner ${company} starts, the sooner you'll see:</p>
          <ul style="padding-left:20px;">
            <li>✅ Real-time project tracking across all sites</li>
            <li>✅ Automated DPRs and RA bills</li>
            <li>✅ Zero material leakage with inventory tracking</li>
          </ul>
          <p style="background:#f0fdf4;padding:16px;border-radius:6px;border-left:4px solid #22c55e;">
            <strong>Quick start offer:</strong> We can set up a pilot on just <em>one project</em> — zero risk, full impact. Go live in 1-2 weeks.
          </p>
          <p>Want me to send you a quotation? Just reply "yes" and I'll have it ready today.</p>`,
          null, null,
          sender.name, sender.replyTo
        )
      };

    case 'quote_followup':
      return {
        subject: `Following Up on Your Onsite Teams Proposal`,
        html: emailWrap(
          `Any Questions About the Proposal, ${firstName}?`,
          `<p>Hi ${firstName},</p>
          <p>I wanted to follow up on the quotation I shared for ${company}. Have you had a chance to review it?</p>
          <p>A few things to keep in mind:</p>
          <ul style="padding-left:20px;">
            <li>💰 Our pricing is <strong>10-20x more affordable</strong> than global ERPs like Procore</li>
            <li>🚀 Implementation takes just <strong>1-2 weeks</strong></li>
            <li>📱 Mobile-first — your site workers can start using it immediately</li>
            <li>🔒 ISO certified with enterprise-grade security</li>
          </ul>
          <p>If you have any questions about pricing, features, or implementation — I'm just a reply away!</p>`,
          'https://www.onsiteteams.com/onsite-pricing', 'View Plans & Pricing',
          sender.name, sender.replyTo
        )
      };

    case 'onboarding_welcome':
      return {
        subject: `Welcome Aboard, ${firstName}! 🎉 Your Onsite Teams Journey Starts Now`,
        html: emailWrap(
          `Welcome to the Onsite Family! 🎉`,
          `<p>Hi ${firstName},</p>
          <p>Congratulations! ${company} is now part of the <strong>Onsite Teams</strong> family — joining 10,000+ companies building smarter.</p>
          <p><strong>What happens next:</strong></p>
          <ol style="padding-left:20px;">
            <li><strong>Setup call</strong> — Our team will reach out within 24 hours to begin onboarding</li>
            <li><strong>Configuration</strong> — We'll customize the platform for your projects</li>
            <li><strong>Training</strong> — Your team gets hands-on training (usually 2-3 sessions)</li>
            <li><strong>Go live</strong> — Start tracking projects in 1-2 weeks!</li>
          </ol>
          <p style="background:#f0f9ff;padding:16px;border-radius:6px;border-left:4px solid #1a0b50;">
            <strong>Your success manager</strong> will be your dedicated contact throughout the onboarding process. Expect a call soon!
          </p>
          <p>Welcome aboard — let's build something great together!</p>`,
          'https://www.onsiteteams.com', 'Get Started',
          sender.name, sender.replyTo
        )
      };

    case 'not_interested':
      return {
        subject: `Thank You for Considering Onsite Teams, ${firstName}`,
        html: emailWrap(
          `Thank You, ${firstName}`,
          `<p>Hi ${firstName},</p>
          <p>Thank you for taking the time to explore Onsite Teams. I understand the timing may not be right for ${company} at the moment.</p>
          <p>Just so you know — our door is always open. Construction technology is evolving fast, and when you're ready, we'll be here to help you:</p>
          <ul style="padding-left:20px;">
            <li>Streamline project management across all sites</li>
            <li>Reduce costs and eliminate wastage</li>
            <li>Get real-time visibility into every project</li>
          </ul>
          <p>Feel free to reach out anytime — even if it's just to ask a question or get an industry insight.</p>
          <p>Wishing you and ${company} all the best! 🙏</p>`,
          null, null,
          sender.name, sender.replyTo
        )
      };

    default:
      return null;
  }
}

// === MAIN POLLING LOGIC ===
const TWENTY_MIN_MS = 20 * 60 * 1000;
const cutoff = new Date(now.getTime() - TWENTY_MIN_MS);
const cutoffStr = `${cutoff.getFullYear()}-${pad(cutoff.getMonth()+1)}-${pad(cutoff.getDate())}T${pad(cutoff.getHours())}:${pad(cutoff.getMinutes())}:${pad(cutoff.getSeconds())}+05:30`;

// Query recently modified leads with email addresses
const changedLeads = await qPage(
  `SELECT id, Full_Name, Company, Phone, Email, Lead_Status, Sales_Stage, Leads_Owner, Modified_Time FROM Leads WHERE Modified_Time >= '${cutoffStr}' AND Email is not null AND Email != '' ORDER BY Modified_Time DESC`,
  500
);

const emailItems = [];
let sent = 0, skipped = 0, noTemplate = 0;

for (const lead of changedLeads) {
  if (!lead.Email || !lead.Email.includes('@')) continue;

  const status = lead.Lead_Status || '';
  const stage = lead.Sales_Stage || '';

  // Determine template
  let templateKey = STATUS_TO_TEMPLATE[status];
  if (!templateKey && STAGE_TO_TEMPLATE[stage]) {
    templateKey = STAGE_TO_TEMPLATE[stage];
  }
  if (!templateKey) { noTemplate++; continue; }

  // Dedup check
  const alreadySent = await sbCheckSent(lead.id, templateKey, status);
  if (alreadySent) { skipped++; continue; }

  // Render
  const sender = getSender(lead, templateKey);
  const rendered = renderTemplate(templateKey, lead, sender);
  if (!rendered) continue;

  // Queue for Gmail Send node — _useTaniya routes to Taniya's Gmail credential
  const useTaniya = (templateKey === 'welcome' || templateKey === 'onboarding_welcome');
  emailItems.push({
    to: lead.Email,
    subject: rendered.subject,
    html: rendered.html,
    fromName: sender.name,
    replyTo: sender.replyTo,
    _useTaniya: useTaniya,
    // Metadata for logging
    _leadId: lead.id,
    _leadEmail: lead.Email,
    _leadName: lead.Full_Name || '',
    _company: lead.Company || '',
    _leadStatus: status,
    _templateKey: templateKey,
    _fromEmail: sender.replyTo,
    _fromName: sender.name,
  });
  sent++;
}

// Log all sends to Supabase (pre-log as 'sending' — Gmail node handles actual delivery)
for (const item of emailItems) {
  await sbLogSent({
    lead_id: item._leadId,
    lead_email: item._leadEmail,
    lead_name: item._leadName,
    company: item._company,
    lead_status: item._leadStatus,
    template_key: item._templateKey,
    from_email: item._fromEmail,
    from_name: item._fromName,
    subject: item.subject,
    status: 'sent'
  });
}

// If no emails to send, return a summary item (Gmail node won't fire)
if (emailItems.length === 0) {
  return [{ json: { status: 'no_emails', checked: changedLeads.length, skipped, noTemplate, cutoff: cutoffStr } }];
}

// Return email items for Gmail Send node
return emailItems.map(item => ({ json: item }));
"""

# === AUTO 11: DEMO REMINDER EMAILS (daily 10 AM) ===
AUTO_11_JS = r"""
// === AUTO 11: DEMO REMINDER EMAILS ===
const SB_URL = '%SUPABASE_URL%';
const SB_KEY = '%SUPABASE_KEY%';
const SB_HEADERS = {'apikey':SB_KEY,'Authorization':`Bearer ${SB_KEY}`,'Content-Type':'application/json','Prefer':'return=minimal'};

const REP_EMAILS = {
  'Dhruv': 'dhruv.tomar@onsiteteams.com', 'Bhavya': 'bhavya.j@onsiteteams.com',
  'Anjali': 'anjali.b@onsiteteams.com', 'Sunil': 'sunil.kumar@onsiteteams.com',
  'Amit U': 'amit.u@onsiteteams.com', 'Mohan': 'mohan.c@onsiteteams.com',
  'Gayatri': 'gayatri.surlkar@onsiteteams.com', 'Shailendra': 'shailendra.g@onsiteteams.com',
  'Amit Kumar': 'amit.k@onsiteteams.com', 'Hitangi': 'hitangi.a@onsiteteams.com',
  'Shruti': 'shruti.a@onsiteteams.com', 'Ravi': 'ravi.gupta@onsiteteams.com',
  'Arthi': 'aparthivarsha@onsiteteams.com', 'Kiran': 'k.kiran@onsiteteams.com',
  'Yogyata': 'yogyata.airi@onsiteteams.com'
};

const DEMO_LINKS = {
  'Anjali': 'https://meet.google.com/hmc-pzdo-jxx',
  'Gayatri': 'https://meet.google.com/gir-uyss-veq',
  'Bhavya': 'https://meet.google.com/vfk-iust-xrj',
  'Shailendra': 'https://meet.google.com/rkm-kphu-tta',
  'Hitangi': 'https://meet.google.com/bpg-wqbb-fbz',
  'Mohan': 'https://meet.google.com/pzr-egje-ffc',
  'Amit U': 'https://meet.google.com/ezu-osvu-zsf',
  'Amit Kumar': 'https://meet.google.com/qsg-gcwi-qrq',
  'Sunil': 'https://meet.google.com/hay-bcrj-uea',
};

// Dedup helpers
async function sbCheckSent(leadId, templateKey, leadStatus) {
  try {
    const resp = await http({method:'GET',
      url:`${SB_URL}/rest/v1/email_sent_log?lead_id=eq.${leadId}&template_key=eq.${encodeURIComponent(templateKey)}&lead_status=eq.${encodeURIComponent(leadStatus)}&select=id&limit=1`,
      headers:{...SB_HEADERS, 'Prefer':''}});
    const data = typeof resp === 'string' ? JSON.parse(resp) : resp;
    return Array.isArray(data) && data.length > 0;
  } catch(e) { return false; }
}

async function sbLogSent(obj) {
  try {
    await http({method:'POST', url:`${SB_URL}/rest/v1/email_sent_log`,
      headers:SB_HEADERS, body:JSON.stringify(obj)});
  } catch(e) { /* non-critical */ }
}

// Tomorrow's date range
const tomorrow = new Date(now.getTime() + 86400000);
const tomorrowStr = `${tomorrow.getFullYear()}-${pad(tomorrow.getMonth()+1)}-${pad(tomorrow.getDate())}`;

// Get leads with demo booked (status = '6. Demo booked')
const demoLeads = await qPage(
  `SELECT id, Full_Name, Company, Phone, Email, Leads_Owner, Lead_Status FROM Leads WHERE Lead_Status = '6. Demo booked' AND Email is not null AND Email != ''`,
  500
);

const emailItems = [];

for (const lead of demoLeads) {
  if (!lead.Email || !lead.Email.includes('@')) continue;

  // Dedup: only one demo_reminder per lead
  const alreadySent = await sbCheckSent(lead.id, 'demo_reminder', '6. Demo booked');
  if (alreadySent) continue;

  const firstName = (lead.Full_Name || 'there').split(' ')[0];
  const ownerRaw = String(lead.Leads_Owner || '').trim();
  const ownerShort = CRM_OWNER_MAP[ownerRaw] || ownerRaw;
  const repEmail = REP_EMAILS[ownerShort] || 'taniya.malhotra@onsiteteams.com';
  const demoLink = DEMO_LINKS[ownerShort] || '';

  const subject = `Reminder: Your Onsite Teams Demo is Tomorrow!`;
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head><body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;background:#f1f5f9;padding:20px 0;">
  <div style="background:linear-gradient(135deg,#1a0b50 0%,#2d1670 100%);padding:28px 24px;text-align:center;border-radius:8px 8px 0 0;">
    <img src="https://www.onsiteteams.com/_next/image?url=%2Fimages%2Flogo-white.webp&w=384&q=75" alt="Onsite Teams" height="36" style="height:36px;">
  </div>
  <div style="background:#ffffff;padding:32px 28px;border-radius:0 0 8px 8px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <h2 style="color:#1a0b50;margin:0 0 16px;font-size:20px;">Your Demo is Tomorrow! ⏰</h2>
    <div style="color:#334155;line-height:1.7;font-size:15px;">
      <p>Hi ${firstName},</p>
      <p>Just a friendly reminder — your <strong>Onsite Teams demo</strong> with <strong>${ownerShort}</strong> is scheduled for tomorrow!</p>
      ${demoLink ? `<p><strong>Join Link:</strong> <a href="${demoLink}" style="color:#6366f1;">${demoLink}</a></p>` : ''}
      <p style="background:#f0f9ff;padding:16px;border-radius:6px;border-left:4px solid #1a0b50;">
        <strong>Quick tips for the demo:</strong><br>
        • Have your current project list handy<br>
        • Think about 1-2 pain points you want solved<br>
        • The demo takes just 15-20 minutes
      </p>
      <p>If you need to reschedule, just reply to this email. See you tomorrow!</p>
    </div>
    ${demoLink ? `<div style="text-align:center;margin:24px 0;"><a href="${demoLink}" style="display:inline-block;background:#c73e5a;color:#ffffff;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:600;font-size:15px;">Join Demo Tomorrow</a></div>` : ''}
  </div>
  <div style="padding:20px 24px;text-align:center;font-size:12px;color:#94a3b8;">
    <p style="margin:4px 0;">${ownerShort} - Onsite Teams | ${repEmail}</p>
    <p style="margin:4px 0;"><a href="https://www.onsiteteams.com" style="color:#6366f1;text-decoration:none;">onsiteteams.com</a></p>
  </div>
</div></body></html>`;

  emailItems.push({
    to: lead.Email,
    subject,
    html,
    fromName: `${ownerShort} - Onsite Teams`,
    replyTo: repEmail,
    _leadId: lead.id, _leadEmail: lead.Email, _leadName: lead.Full_Name || '',
    _company: lead.Company || '', _leadStatus: '6. Demo booked',
    _templateKey: 'demo_reminder', _fromEmail: repEmail, _fromName: `${ownerShort} - Onsite Teams`,
  });
}

// Log to Supabase
for (const item of emailItems) {
  await sbLogSent({
    lead_id: item._leadId, lead_email: item._leadEmail, lead_name: item._leadName,
    company: item._company, lead_status: item._leadStatus, template_key: item._templateKey,
    from_email: item._fromEmail, from_name: item._fromName, subject: item.subject, status: 'sent'
  });
}

if (emailItems.length === 0) {
  return [{ json: { status: 'no_reminders', checked: demoLeads.length, date: tomorrowStr } }];
}

return emailItems.map(item => ({ json: item }));
"""

# === AUTO 12: FIREFLIES MEETING NOTES → ZOHO CRM ===
# Webhook receives Fireflies event, fetches transcript, matches to Zoho lead, updates CRM.
AUTO_12_JS = r"""
// === AUTO 12: FIREFLIES → ZOHO CRM ===
const body = $input.first().json.body || $input.first().json;
let transcriptId = body?.data?.transcriptId || body?.transcriptId || '';
const meetingId = body?.meetingId || body?.data?.meetingId || '';

const FF_KEY = '%FIREFLIES_API_KEY%';

// Fetch full transcript details from Fireflies GraphQL API
async function ffQuery(query, variables) {
  const resp = await http({
    method: 'POST',
    url: 'https://api.fireflies.ai/graphql',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${FF_KEY}` },
    body: JSON.stringify({ query, variables: variables || {} }),
  });
  return typeof resp === 'string' ? JSON.parse(resp) : resp;
}

// If no transcriptId but we have meetingId, look up the transcript
if (!transcriptId && meetingId) {
  try {
    const lookup = await ffQuery(`
      query {
        transcripts(limit: 10) {
          id title date
        }
      }
    `);
    const allTranscripts = lookup?.data?.transcripts || [];
    const match = allTranscripts.find(t => t.id === meetingId);
    if (match) {
      transcriptId = match.id;
    }
  } catch (e) {
    // Lookup failed — fall through to meetingId fallback
  }
}

// If we still have no transcriptId, try using meetingId directly as transcript ID
if (!transcriptId && meetingId) {
  transcriptId = meetingId;
}

if (!transcriptId) {
  return [{ json: { status: 'no_transcript_id', body, meetingId } }];
}

// Get transcript details
const result = await ffQuery(`
  query($id: String!) {
    transcript(id: $id) {
      id title date duration organizer_email
      participants
      summary {
        action_items overview shorthand_bullet keywords
      }
    }
  }
`, { id: transcriptId });

const tr = result?.data?.transcript;
if (!tr) {
  return [{ json: { status: 'transcript_not_found', transcriptId } }];
}

// Parse meeting title to extract rep name — "Onsite App Demo (Gayatri)" or "Onsite<>CompanyName"
const title = tr.title || '';
const durationMin = Math.round(tr.duration || 0);
const meetDate = tr.date ? new Date(tr.date).toISOString().split('T')[0] : TODAY;

// Extract rep name from title patterns
let repName = '';
const repMatch = title.match(/Demo\s*\(([^)]+)\)/i) || title.match(/Demo[-\s]*([A-Za-z]+)/i);
if (repMatch) repName = repMatch[1].trim();

// Reverse-map Google Meet link code to rep name (each rep has a static Meet link)
if (!repName) {
  const MEET_CODE_TO_REP = {
    'hmc-pzdo-jxx': 'Anjali',
    'gir-uyss-veq': 'Gayatri',
    'vfk-iust-xrj': 'Bhavya',
    'rkm-kphu-tta': 'Shailendra',
    'bpg-wqbb-fbz': 'Hitangi',
    'pzr-egje-ffc': 'Mohan',
    'ezu-osvu-zsf': 'Amit U',
    'qsg-gcwi-qrq': 'Amit Kumar',
    'hay-bcrj-uea': 'Sunil',
  };
  // Fireflies titles often contain the Meet code, e.g. "Meet – bpg-wqbb-fbz" or "meet.google.com/bpg-wqbb-fbz"
  const titleLower = title.toLowerCase();
  for (const [code, rep] of Object.entries(MEET_CODE_TO_REP)) {
    if (titleLower.includes(code)) { repName = rep; break; }
  }
}

// Get participant emails — split into Onsite team vs external (potential lead)
const participants = tr.participants || [];
const onsiteEmailDomains = ['gittigo.com', 'onsiteteams.com'];
const isOnsiteEmail = (e) => e && onsiteEmailDomains.some(d => e.toLowerCase().includes(d));
const externalEmails = participants.filter(e => e && !isOnsiteEmail(e));
const teamEmails = participants.filter(e => isOnsiteEmail(e));

// Strategy: If rep still unknown (Calendly = unique Meet link each time),
// identify rep from their @onsiteteams.com participant email
if (!repName && teamEmails.length > 0) {
  const EMAIL_TO_REP = {
    'dhruv.tomar@onsiteteams.com': 'Dhruv',
    'bhavya.j@onsiteteams.com': 'Bhavya',
    'anjali.b@onsiteteams.com': 'Anjali',
    'sunil.kumar@onsiteteams.com': 'Sunil',
    'amit.u@onsiteteams.com': 'Amit U',
    'mohan.c@onsiteteams.com': 'Mohan',
    'gayatri.surlkar@onsiteteams.com': 'Gayatri',
    'shailendra.g@onsiteteams.com': 'Shailendra',
    'amit.k@onsiteteams.com': 'Amit Kumar',
    'hitangi.a@onsiteteams.com': 'Hitangi',
    'shruti.a@onsiteteams.com': 'Shruti',
    'ravi.gupta@onsiteteams.com': 'Ravi',
    'aparthivarsha@onsiteteams.com': 'Arthi',
    'k.kiran@onsiteteams.com': 'Kiran',
    'yogyata.airi@onsiteteams.com': 'Yogyata',
    'taniya.malhotra@onsiteteams.com': 'Taniya',
  };
  for (const te of teamEmails) {
    const match = EMAIL_TO_REP[te.toLowerCase()];
    // Skip non-sales emails (Dhruv = AI engineer, Taniya = marketing, onsitedemo = bot)
    if (match && match !== 'Dhruv' && match !== 'Taniya') { repName = match; break; }
  }
  // If only Dhruv/Taniya found, still use them as fallback
  if (!repName) {
    for (const te of teamEmails) {
      const match = EMAIL_TO_REP[te.toLowerCase()];
      if (match) { repName = match; break; }
    }
  }
}

// Build meeting notes for CRM
const overview = tr.summary?.overview || '';
const actionItems = tr.summary?.action_items || '';
const keywords = (tr.summary?.keywords || []).join(', ');
const bullets = tr.summary?.shorthand_bullet || '';

// Format a concise CRM note
let crmNote = `\n--- MEETING NOTES (${meetDate}) ---\n`;
crmNote += `Meeting: ${title}\n`;
crmNote += `Duration: ${durationMin} min\n`;
if (repName) crmNote += `Rep: ${repName}\n`;
if (keywords) crmNote += `Topics: ${keywords}\n`;
crmNote += `\n`;

if (overview) {
  // Clean markdown formatting for plain text CRM field
  const cleanOverview = overview.replace(/\*\*/g, '').replace(/- /g, '• ');
  crmNote += `SUMMARY:\n${cleanOverview}\n\n`;
}

if (actionItems) {
  const cleanActions = actionItems.replace(/\*\*/g, '').replace(/- /g, '• ').trim();
  crmNote += `ACTION ITEMS:\n${cleanActions}\n`;
}

crmNote += `\n--- End Meeting Notes ---`;

// Try to match external participant emails to Zoho leads
const matchedLeads = [];

// Strategy 1: Match by participant email
for (const email of externalEmails) {
  const leads = await qPage(
    `SELECT id, Full_Name, Company, Email, Phone, Lead_Status, Sales_Stage, Description, Leads_Owner FROM Leads WHERE Email = '${email.replace(/'/g, "''")}'`,
    10
  );
  matchedLeads.push(...leads);
}

// Strategy 2: If title has company name "Onsite<>CompanyName", search by company
if (matchedLeads.length === 0) {
  const companyMatch = title.match(/Onsite\s*<>\s*(.+?)(?:\s*['"]|$)/i);
  if (companyMatch) {
    const companyName = companyMatch[1].trim();
    const leads = await qPage(
      `SELECT id, Full_Name, Company, Email, Phone, Lead_Status, Sales_Stage, Description, Leads_Owner FROM Leads WHERE Company like '%${companyName.replace(/'/g, "''").replace(/%/g, '')}%' AND Lead_Status not in ('Junk Lead', '11. Rejected')`,
      10
    );
    matchedLeads.push(...leads);
  }
}

// Strategy 3: If we have a rep name, search for RECENTLY MODIFIED Demo Booked leads (last 4 hours)
// Only auto-update if exactly 1 match. If multiple, send WhatsApp asking rep to confirm.
let strategy3Ambiguous = false;
if (matchedLeads.length === 0 && repName) {
  const primaryOwner = CRM_PRIMARY[repName];
  if (primaryOwner) {
    const ownerFilter = `Leads_Owner = '${primaryOwner}'`;
    const fourHoursAgo = new Date(now.getTime() - 4 * 60 * 60 * 1000);
    const cutoff4h = `${fourHoursAgo.getFullYear()}-${pad(fourHoursAgo.getMonth()+1)}-${pad(fourHoursAgo.getDate())}T${pad(fourHoursAgo.getHours())}:${pad(fourHoursAgo.getMinutes())}:00+05:30`;
    const leads = await qPage(
      `SELECT id, Full_Name, Company, Email, Phone, Lead_Status, Sales_Stage, Description, Leads_Owner FROM Leads WHERE (${ownerFilter}) AND Lead_Status in ('6. Demo booked', '7. Demo done') AND Modified_Time >= '${cutoff4h}' ORDER BY Modified_Time DESC`,
      10
    );
    if (leads.length === 1) {
      matchedLeads.push(leads[0]);
    } else if (leads.length > 1) {
      strategy3Ambiguous = true;
      // Don't auto-update — ask rep via WhatsApp which lead
      const repPhone = REPS[repName] || ALL_TEAM[repName];
      if (repPhone) {
        let askMsg = `📝 Fireflies recorded your demo (${durationMin} min) but I couldn't identify which lead it was.\n\nRecent leads:\n`;
        leads.slice(0, 5).forEach((l, i) => {
          askMsg += `${i+1}. ${l.Full_Name} — ${l.Company || '?'}\n`;
        });
        askMsg += `\nReply with the number and I'll save the meeting notes to their CRM record.\n— Onsite Pulse`;
        await wa(repPhone, askMsg, repName);
      }
    }
  }
}

// Update matched leads in Zoho CRM — add as a Note (not Description)
const updates = [];
const uniqueLeadIds = [...new Set(matchedLeads.map(l => l.id))];

for (const leadId of uniqueLeadIds.slice(0, 5)) {
  const lead = matchedLeads.find(l => l.id === leadId);
  const noteTitle = `Demo Notes — ${meetDate} — ${title}`;

  try {
    const t = await getToken();
    await http({
      method: 'POST',
      url: `https://www.zohoapis.in/crm/v7/Leads/${leadId}/Notes`,
      headers: { Authorization: `Zoho-oauthtoken ${t}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: [{ Note_Title: noteTitle, Note_Content: crmNote }] }),
    });
    updates.push({ leadId, name: lead.Full_Name, company: lead.Company, status: 'updated' });
  } catch (e) {
    updates.push({ leadId, name: lead.Full_Name, status: 'failed', error: e.message });
  }
}

// Also notify the rep via WhatsApp if we identified them
if (repName && updates.length > 0) {
  const repPhone = REPS[repName] || ALL_TEAM[repName];
  if (repPhone) {
    const okUpdates = updates.filter(u => u.status === 'updated');
    let leadLines = '';
    for (const u of okUpdates) {
      const lead = matchedLeads.find(l => l.id === u.leadId);
      const phone = lead?.Phone || lead?.Mobile || '';
      leadLines += `• ${u.name} (${u.company || '?'})${phone ? ' | ' + phone : ''}\n`;
    }
    // Extract top 3 action items from transcript
    let actionsSnippet = '';
    if (actionItems) {
      const lines = actionItems.split('\n').filter(l => l.trim() && !l.startsWith('**'));
      actionsSnippet = lines.slice(0, 3).map(l => l.replace(/\*\*/g, '').trim()).join('\n');
      if (actionsSnippet) actionsSnippet = `\nKey Actions:\n${actionsSnippet}\n`;
    }
    const msg = `📝 Meeting notes auto-saved!\n\nMeeting: ${title}\nDuration: ${durationMin} min\nTopics: ${keywords || 'N/A'}\n\nCRM updated for:\n${leadLines}${actionsSnippet}\n— Onsite Pulse`;
    await wa(repPhone, msg, repName);
  }
}

return [{ json: {
  status: strategy3Ambiguous ? 'ambiguous_asked_rep' : 'processed',
  transcriptId,
  title,
  duration: durationMin,
  repName,
  externalEmails,
  matchedLeads: uniqueLeadIds.length,
  updates,
} }];
"""

# === AUTOMATION 13: Follow-Up Reminder (5 min before exact time) ===
AUTO_13_JS = r"""
// === AUTOMATION 13: Follow-Up Reminder — 5 min before ===
// Runs every 5 min, 8 AM - 8 PM IST Mon-Sat
// Sends personalized WhatsApp alert to rep whose follow-up is 5 min away

function fmtTime(dt) {
  if (!dt) return '';
  const m = String(dt).match(/T(\d{2}):(\d{2})/);
  if (!m) return '';
  let h = parseInt(m[1]), mn = m[2];
  const ap = h >= 12 ? 'PM' : 'AM';
  if (h > 12) h -= 12;
  if (h === 0) h = 12;
  return `${h}:${mn} ${ap}`;
}

function getDealOwner(l) {
  const raw = String(l.Leads_Owner || '').trim();
  return CRM_OWNER_MAP[raw] || raw || 'Unassigned';
}

const ALL_PHONES = {...REPS, ...PRE_SALES};
function findRep(shortName) {
  if (!shortName || shortName === 'Team' || shortName === 'Unassigned') return null;
  if (TEST_MODE) return {phone: TEST_PHONE, name: shortName + ' [TEST]'};
  if (ALL_PHONES[shortName]) return {phone: ALL_PHONES[shortName], name: shortName};
  return null;
}

// Current IST time
const istNow = new Date(now.getTime() + 5.5 * 3600000);
const istHour = istNow.getHours();

// Only during business hours
if (istHour < 8 || istHour >= 20) {
  return [{ json: { skipped: true, reason: 'outside business hours' } }];
}

// Window: 5 min to 10 min from now (catches follow-ups ~5 min away)
const winStart = new Date(istNow.getTime() + 5 * 60000);
const winEnd = new Date(istNow.getTime() + 10 * 60000 - 1000); // -1s to avoid overlap

const fmtISO = (d) => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}+05:30`;

const startStr = fmtISO(winStart);
const endStr = fmtISO(winEnd);

// Query follow-ups in this window (exclude demo booked — those get a separate 10-min reminder)
const leads = await qPage(
  `SELECT Company, Full_Name, Phone, Lead_Task, Sales_Stage, Lead_Status, Leads_Owner FROM Leads WHERE Lead_Task between '${startStr}' and '${endStr}' AND Lead_Status not in ('6. Demo booked', '12. Subscribed', '11. Rejected', '10. Not Interested (Not Potential)', 'Junk Lead')`
);

if (leads.length === 0) {
  return [{ json: { skipped: true, followups: 0, window: `${startStr} → ${endStr}` } }];
}

// Group by owner
const byOwner = {};
leads.forEach(l => {
  const o = getDealOwner(l);
  if (!byOwner[o]) byOwner[o] = [];
  byOwner[o].push(l);
});

let sent = 0;
for (const [owner, ownerLeads] of Object.entries(byOwner)) {
  const rep = findRep(owner);
  if (!rep) continue;

  let msg = `*${rep.name}, follow-up in 5 min!*\n\n`;
  ownerLeads.forEach((l, i) => {
    const co = l.Company || l.Full_Name || '?';
    const time = fmtTime(l.Lead_Task);
    const st = l.Sales_Stage || l.Lead_Status || '';
    const contact = l.Phone || '';
    msg += `${i+1}. *${co}* — ${time}`;
    if (st) msg += ` (${st})`;
    if (contact) msg += `\n   ${contact}`;
    msg += '\n';
  });
  msg += `\n_Onsite Pulse_`;
  await wa(rep.phone, msg, rep.name);
  sent++;
}

return [{ json: { sent, total: leads.length, window: `${startStr} → ${endStr}` } }];
"""

# === AUTOMATION 14: Demo Reminder (10 min before demo starts) ===
AUTO_14_JS = r"""
// === AUTOMATION 14: Demo Reminder — 10 min before ===
// Runs every 5 min, 8 AM - 8 PM IST Mon-Sat
// Sends WhatsApp alert to rep whose demo is 10 min away

function fmtTime(dt) {
  if (!dt) return '';
  const m = String(dt).match(/T(\d{2}):(\d{2})/);
  if (!m) return '';
  let h = parseInt(m[1]), mn = m[2];
  const ap = h >= 12 ? 'PM' : 'AM';
  if (h > 12) h -= 12;
  if (h === 0) h = 12;
  return `${h}:${mn} ${ap}`;
}

function getDealOwner(l) {
  const raw = String(l.Leads_Owner || '').trim();
  return CRM_OWNER_MAP[raw] || raw || 'Unassigned';
}

const ALL_PHONES = {...REPS, ...PRE_SALES};
function findRep(shortName) {
  if (!shortName || shortName === 'Team' || shortName === 'Unassigned') return null;
  if (TEST_MODE) return {phone: TEST_PHONE, name: shortName + ' [TEST]'};
  if (ALL_PHONES[shortName]) return {phone: ALL_PHONES[shortName], name: shortName};
  return null;
}

// Current IST time
const istNow = new Date(now.getTime() + 5.5 * 3600000);
const istHour = istNow.getHours();

if (istHour < 8 || istHour >= 20) {
  return [{ json: { skipped: true, reason: 'outside business hours' } }];
}

// Window: 10 min to 15 min from now (catches demos ~10 min away)
const winStart = new Date(istNow.getTime() + 10 * 60000);
const winEnd = new Date(istNow.getTime() + 15 * 60000 - 1000);

const fmtISO = (d) => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}+05:30`;

const startStr = fmtISO(winStart);
const endStr = fmtISO(winEnd);

// Query demo booked leads with Lead_Task (demo time) in this window
const leads = await qPage(
  `SELECT Company, Full_Name, Phone, Email, Lead_Task, Sales_Stage, Lead_Source, Leads_Owner FROM Leads WHERE Lead_Status = '6. Demo booked' AND Demo_Done_Date is null AND Lead_Task between '${startStr}' and '${endStr}'`
);

if (leads.length === 0) {
  return [{ json: { skipped: true, demos: 0, window: `${startStr} → ${endStr}` } }];
}

// Group by owner
const byOwner = {};
leads.forEach(l => {
  const o = getDealOwner(l);
  if (!byOwner[o]) byOwner[o] = [];
  byOwner[o].push(l);
});

let sent = 0;
for (const [owner, ownerLeads] of Object.entries(byOwner)) {
  const rep = findRep(owner);
  if (!rep) continue;

  let msg = `*${rep.name}, demo in 10 min!*\n\n`;
  ownerLeads.forEach((l, i) => {
    const co = l.Company || l.Full_Name || '?';
    const time = fmtTime(l.Lead_Task);
    const contact = l.Phone || l.Email || '';
    const source = l.Lead_Source || '';
    msg += `${i+1}. *${co}* — ${time}`;
    if (source) msg += ` (${source})`;
    if (contact) msg += `\n   ${contact}`;
    msg += '\n';
  });
  msg += `\nPrepare your demo setup & check CRM notes!\n_Onsite Pulse_`;
  await wa(rep.phone, msg, rep.name);
  sent++;
}

// Also notify managers if any demos are happening
if (leads.length > 0) {
  const repNames = [...new Set(leads.map(l => getDealOwner(l)))].join(', ');
  const mgrMsg = `*${leads.length} demo${leads.length > 1 ? 's' : ''} starting in ~10 min*\nReps: ${repNames}\n\n`;
  let details = '';
  leads.forEach(l => {
    const co = l.Company || l.Full_Name || '?';
    const owner = getDealOwner(l);
    const time = fmtTime(l.Lead_Task);
    details += `• ${co} (${owner}) — ${time}\n`;
  });
  await waAll(MGR, mgrMsg + details + `\n_Onsite Pulse_`);
}

return [{ json: { sent, total: leads.length, window: `${startStr} → ${endStr}` } }];
"""

# === WORKFLOW DEFINITIONS ===

WORKFLOWS = {
    "1": {
        "name": "Onsite: Follow-Up Alerts",
        "cron": "0 8-20 * * 1-6",  # Hourly 8 AM - 8 PM IST, Mon-Sat
        "js": AUTO_1_JS,
        "description": "Hourly 8 AM-8 PM Mon-Sat — Follow-up alerts (full briefing at 8 AM, hourly nudges after)",
    },
    "2": {
        "name": "Onsite: Demo Stuck Alert",
        "cron": "0 9 * * *",  # Daily 9 AM IST
        "js": AUTO_2_JS,
        "description": "Daily 9 AM — Leads stuck in 'Demo Booked' status",
    },
    "3": {
        "name": "Onsite: Daily Scorecard",
        "cron": "30 9 * * 1-6",  # Daily 9:30 AM IST, Mon-Sat
        "js": AUTO_3_JS,
        "description": "Daily 9:30 AM — Morning kickoff template + MTD scorecard",
    },
    "4": {
        "name": "Onsite: CRM Hygiene Report",
        "cron": "0 17 * * 5",  # Friday 5 PM IST
        "js": AUTO_4_JS,
        "description": "Friday 5 PM — CRM data quality report",
    },
    "5": {
        "name": "Onsite: Hot Source Alert",
        "cron": "0 8,14 * * 1-6",  # 8 AM + 2 PM IST, Mon-Sat
        "js": AUTO_5_JS,
        "description": "8 AM + 2 PM Mon-Sat — Website & WhatsApp lead priority alerts",
    },
    "6": {
        "name": "Onsite: Ad Fatigue Alert",
        "cron": "0 9 * * 1",  # Monday 9 AM IST
        "js": AUTO_6_JS,
        "description": "Monday 9 AM — Facebook ad fatigue & dying campaign alerts",
    },
    "7": {
        "name": "Onsite: Daily Session Opener",
        "cron": "30 9 * * 1-6",  # 9:30 AM IST Mon-Sat
        "js": AUTO_7_JS,
        "description": "9:30 AM Mon-Sat — Sends personalized morning kickoff template to team",
    },
    "8": {
        "name": "Onsite: Pulse Bot",
        "webhook": True,
        "webhook_path": "onsite-pulse-bot",
        "js": AUTO_8_JS,
        "description": "Webhook — Interactive WhatsApp bot (responds to team messages)",
    },
    "9": {
        "name": "Onsite: Pulse Chat",
        "webhook": True,
        "webhook_path": "pulse-chat",
        "js": AUTO_9_JS,
        "description": "Webhook — Web chat interface for team to query their CRM data",
    },
    "10": {
        "name": "Onsite: Auto Email Pipeline",
        "cron": "*/15 8-20 * * 1-6",  # Every 15 min, 8 AM - 8 PM IST, Mon-Sat
        "js": AUTO_10_JS,
        "email": True,  # Dual Gmail: Taniya (welcome/onboarding) + Dhruv (rep emails)
        "description": "Every 15 min Mon-Sat — Pipeline emails on Zoho CRM status changes",
    },
    "11": {
        "name": "Onsite: Demo Reminder Emails",
        "cron": "0 10 * * 1-6",  # Daily 10 AM IST, Mon-Sat
        "js": AUTO_11_JS,
        "email": True,
        "description": "Daily 10 AM — Reminder emails for upcoming demos",
    },
    "12": {
        "name": "Onsite: Fireflies Meeting Notes",
        "webhook": True,
        "webhook_path": "fireflies-notes",
        "js": AUTO_12_JS,
        "description": "Webhook — Fireflies transcription → Zoho CRM lead notes + WhatsApp notification",
    },
    "13": {
        "name": "Onsite: Follow-Up Reminder (5 min)",
        "cron": "*/5 8-20 * * 1-6",  # Every 5 min, 8 AM - 8 PM IST, Mon-Sat
        "js": AUTO_13_JS,
        "description": "Every 5 min Mon-Sat — WhatsApp reminder 5 min before each follow-up time",
    },
    "14": {
        "name": "Onsite: Demo Reminder (10 min)",
        "cron": "*/5 8-20 * * 1-6",  # Every 5 min, 8 AM - 8 PM IST, Mon-Sat
        "js": AUTO_14_JS,
        "description": "Every 5 min Mon-Sat — WhatsApp reminder 10 min before each demo starts",
    },
}


def get_fb_token():
    """Try to read FB token from various sources."""
    import os
    # Try .env
    env_path = "/Volumes/Dhruv_SSD/AIwithDhruv/Claude/Onsite/sales-intelligence/backend/.env"
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith("FB_ACCESS_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"')
    except FileNotFoundError:
        pass

    # Try MCP settings
    settings_path = os.path.expanduser("~/.claude/projects/-Volumes-Dhruv-SSD-AIwithDhruv-Claude/settings.json")
    try:
        import json as j
        with open(settings_path) as f:
            settings = j.load(f)
            for server in settings.get("mcpServers", {}).values():
                env = server.get("env", {})
                if "FB_ACCESS_TOKEN" in env:
                    return env["FB_ACCESS_TOKEN"]
    except (FileNotFoundError, Exception):
        pass

    return ""


def build_workflow_json(num: str) -> dict:
    """Build n8n workflow JSON for a given automation number."""
    import uuid
    wf = WORKFLOWS[num]
    js_code = SHARED_JS + wf["js"]

    # Inject credentials from environment
    _env_replacements = {
        "%ZOHO_CID%": os.environ.get("ZOHO_CID", ""),
        "%ZOHO_CS%": os.environ.get("ZOHO_CS", ""),
        "%ZOHO_RT%": os.environ.get("ZOHO_RT", ""),
        "%GALLABOX_KEY%": os.environ.get("GALLABOX_KEY", ""),
        "%GALLABOX_SECRET%": os.environ.get("GALLABOX_SECRET", ""),
        "%GALLABOX_CHANNEL%": os.environ.get("GALLABOX_CHANNEL", ""),
        "%SUPABASE_URL%": os.environ.get("SUPABASE_URL", ""),
        "%SUPABASE_KEY%": os.environ.get("SUPABASE_KEY", ""),
        "%OPENROUTER_KEY%": os.environ.get("OPENROUTER_KEY", ""),
        "%FIREFLIES_API_KEY%": os.environ.get("FIREFLIES_API_KEY", ""),
    }
    for placeholder, value in _env_replacements.items():
        js_code = js_code.replace(placeholder, value)

    # Inject FB token for automation 6
    if num == "6":
        fb_token = get_fb_token()
        js_code = js_code.replace("%FB_TOKEN%", fb_token)

    # Webhook-triggered workflow (e.g., interactive bot)
    if wf.get("webhook"):
        return {
            "name": wf["name"],
            "nodes": [
                {
                    "parameters": {
                        "httpMethod": "POST",
                        "path": wf["webhook_path"],
                        "responseMode": "responseNode",
                    },
                    "name": "Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 2,
                    "position": [0, 0],
                    "id": str(uuid.uuid4()),
                    "webhookId": str(uuid.uuid4()),
                },
                {
                    "parameters": {
                        "mode": "runOnceForAllItems",
                        "jsCode": js_code,
                    },
                    "name": "Run Automation",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [300, 0],
                    "id": str(uuid.uuid4()),
                },
                {
                    "parameters": {
                        "respondWith": "json",
                        "responseBody": "={{ $json }}",
                    },
                    "name": "Respond",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "typeVersion": 1.1,
                    "position": [600, 0],
                    "id": str(uuid.uuid4()),
                },
            ],
            "connections": {
                "Webhook": {
                    "main": [
                        [{"node": "Run Automation", "type": "main", "index": 0}]
                    ]
                },
                "Run Automation": {
                    "main": [
                        [{"node": "Respond", "type": "main", "index": 0}]
                    ]
                },
            },
            "settings": {
                "executionOrder": "v1",
                "timezone": "Asia/Kolkata",
                "availableInMCP": True,
            },
        }

    # Email workflow: Schedule → Code → IF → Gmail Taniya / Gmail Rep
    # Taniya's credential sends welcome + onboarding emails
    # Dhruv's credential sends all other rep emails (with Reply-To set to actual rep)
    if wf.get("email"):
        gmail_params = {
            "sendTo": "={{ $json.to }}",
            "subject": "={{ $json.subject }}",
            "emailType": "html",
            "message": "={{ $json.html }}",
            "options": {
                "replyTo": "={{ $json.replyTo }}",
                "senderName": "={{ $json.fromName }}",
            },
        }
        return {
            "name": wf["name"],
            "nodes": [
                {
                    "parameters": {
                        "rule": {
                            "interval": [
                                {"field": "cronExpression", "expression": wf["cron"]}
                            ]
                        }
                    },
                    "name": "Schedule",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "typeVersion": 1.3,
                    "position": [0, 0],
                    "id": str(uuid.uuid4()),
                },
                {
                    "parameters": {
                        "mode": "runOnceForAllItems",
                        "jsCode": js_code,
                    },
                    "name": "Run Automation",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [300, 0],
                    "id": str(uuid.uuid4()),
                },
                {
                    "parameters": {
                        "conditions": {
                            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                            "conditions": [
                                {
                                    "id": str(uuid.uuid4()),
                                    "leftValue": "={{ $json._useTaniya }}",
                                    "rightValue": True,
                                    "operator": {
                                        "type": "boolean",
                                        "operation": "true",
                                    },
                                }
                            ],
                            "combinator": "and",
                        },
                    },
                    "name": "Is Taniya?",
                    "type": "n8n-nodes-base.if",
                    "typeVersion": 2,
                    "position": [600, 0],
                    "id": str(uuid.uuid4()),
                },
                {
                    "parameters": gmail_params,
                    "name": "Gmail Taniya",
                    "type": "n8n-nodes-base.gmail",
                    "typeVersion": 2.1,
                    "position": [900, -100],
                    "id": str(uuid.uuid4()),
                    "credentials": {
                        "gmailOAuth2": {
                            "id": "iCNfKJ9SVwZmUwua",
                            "name": "taniya.malhotra@onsiteteams.com",
                        }
                    },
                },
                {
                    "parameters": gmail_params,
                    "name": "Gmail Rep",
                    "type": "n8n-nodes-base.gmail",
                    "typeVersion": 2.1,
                    "position": [900, 100],
                    "id": str(uuid.uuid4()),
                    "credentials": {
                        "gmailOAuth2": {
                            "id": "arJIUR0ESDgNcuov",
                            "name": "dhruv.tomar_updated",
                        }
                    },
                },
            ],
            "connections": {
                "Schedule": {
                    "main": [
                        [{"node": "Run Automation", "type": "main", "index": 0}]
                    ]
                },
                "Run Automation": {
                    "main": [
                        [{"node": "Is Taniya?", "type": "main", "index": 0}]
                    ]
                },
                "Is Taniya?": {
                    "main": [
                        [{"node": "Gmail Taniya", "type": "main", "index": 0}],
                        [{"node": "Gmail Rep", "type": "main", "index": 0}],
                    ]
                },
            },
            "settings": {
                "executionOrder": "v1",
                "timezone": "Asia/Kolkata",
                "availableInMCP": True,
            },
        }

    # Schedule-triggered workflow (default)
    return {
        "name": wf["name"],
        "nodes": [
            {
                "parameters": {
                    "rule": {
                        "interval": [
                            {"field": "cronExpression", "expression": wf["cron"]}
                        ]
                    }
                },
                "name": "Schedule",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.3,
                "position": [0, 0],
                "id": str(uuid.uuid4()),
            },
            {
                "parameters": {
                    "mode": "runOnceForAllItems",
                    "jsCode": js_code,
                },
                "name": "Run Automation",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [300, 0],
                "id": str(uuid.uuid4()),
            },
        ],
        "connections": {
            "Schedule": {
                "main": [
                    [{"node": "Run Automation", "type": "main", "index": 0}]
                ]
            }
        },
        "settings": {
            "executionOrder": "v1",
            "timezone": "Asia/Kolkata",
            "availableInMCP": True,
        },
    }


def deploy_workflow(num: str) -> dict:
    """Deploy a workflow to n8n via REST API."""
    wf_json = build_workflow_json(num)
    wf = WORKFLOWS[num]

    data = json.dumps(wf_json).encode()
    headers = {
        "Content-Type": "application/json",
        "X-N8N-API-KEY": N8N_API_KEY,
    }
    req = urllib.request.Request(
        f"{N8N_HOST}/api/v1/workflows",
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        wf_id = result.get("id", "?")
        print(f"  OK — {wf['name']} → ID: {wf_id}")
        return result
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  FAILED — {wf['name']}: {e} | {body[:200]}")
        return {"error": str(e), "body": body}


def activate_workflow(wf_id: str) -> dict:
    """Activate a workflow by ID."""
    headers = {
        "Content-Type": "application/json",
        "X-N8N-API-KEY": N8N_API_KEY,
    }
    req = urllib.request.Request(
        f"{N8N_HOST}/api/v1/workflows/{wf_id}/activate",
        headers=headers,
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": str(e)}


def list_onsite_workflows():
    """List existing Onsite workflows on n8n."""
    headers = {"X-N8N-API-KEY": N8N_API_KEY}
    req = urllib.request.Request(f"{N8N_HOST}/api/v1/workflows?limit=100", headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        workflows = result.get("data", [])
        onsite = [w for w in workflows if w.get("name", "").startswith("Onsite:")]
        if onsite:
            print(f"\n=== ONSITE WORKFLOWS ON N8N ({len(onsite)}) ===\n")
            for w in onsite:
                status = "ACTIVE" if w.get("active") else "INACTIVE"
                print(f"  [{status}] {w['name']} (ID: {w['id']})")
        else:
            print("\nNo Onsite workflows found on n8n.")
        return onsite
    except urllib.error.HTTPError as e:
        print(f"Error: {e}")
        return []


def main():
    args = sys.argv[1:]

    if "--list" in args:
        list_onsite_workflows()
        return

    # Which to deploy
    nums = [a for a in args if a.isdigit() and a in WORKFLOWS]
    if not nums:
        nums = list(WORKFLOWS.keys())

    print(f"=== DEPLOYING {len(nums)} ONSITE WORKFLOWS TO N8N ===\n")
    print(f"Target: {N8N_HOST}\n")

    results = {}
    for num in nums:
        wf = WORKFLOWS[num]
        print(f"[{num}] {wf['name']} — {wf['description']}")
        print(f"    Schedule: {wf.get('cron', 'webhook')}")
        result = deploy_workflow(num)
        results[num] = result

    print(f"\n{'='*60}")
    print(f"Deployed {len(nums)} workflows (all INACTIVE)")
    print(f"Go to {N8N_HOST} to review and activate them.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
