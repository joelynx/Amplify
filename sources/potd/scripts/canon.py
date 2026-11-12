# Canonical competition table: key -> attributes.
# C(key, full_name, country_or_region, kind, conf, note, bank, group)
# group=None means "derive from country" (country group if the country is big enough, else region group).

CANON = {}

def C(key, full, country, kind, conf='high', note='', bank='', group=None):
    CANON[key] = dict(full=full, country=country, kind=kind, conf=conf, note=note, bank=bank, group=group)

MODS = 'Math Olympiad Discord Server'
MOCK = 'Mock Olympiads'
ONLINE = 'Online Community Contests'
UNI = 'University Mathematics Competitions'
INTL = 'International Olympiads'
EUR = 'Other European Olympiads'
ASIA = 'Other Asian Olympiads'
LATAM = 'Latin American Olympiads'
AFR = 'African Olympiads'
BOOKS = 'Problem Books and Journals'
EXAMS = 'School and Admission Exams'
PROG = 'Programming Contests'
UNID = 'Unidentified Contests'

# ---------------- international ----------------
C('IMO', 'International Mathematical Olympiad', 'International', 'international', group=INTL)
C('IMOSL', 'International Mathematical Olympiad Shortlist', 'International', 'international', group=INTL,
  note='Includes one "Generalization of 2001 IMOSL, C1" row (marked generalised in the subsource).')
C('IMO_LL', 'International Mathematical Olympiad Longlist', 'International', 'international', 'medium', group=INTL,
  note='"West German proposal for 1978 IMO" is a proposed (longlist) problem; filed here.')
C('EGMO', "European Girls' Mathematical Olympiad", 'International', 'international', group=INTL)
C('APMO', 'Asian Pacific Mathematics Olympiad', 'International', 'international', group=INTL,
  note='Official name; the sheet\'s acronym list says "Asia Pacific Mathematical Olympiad".')
C('BALKAN', 'Balkan Mathematical Olympiad', 'Europe (regional)', 'international', group=EUR,
  note='"Balkan MO"/"BalkanMO". Not the British BMO1/BMO2.')
C('BALKAN_SL', 'Balkan Mathematical Olympiad Shortlist', 'Europe (regional)', 'international', group=EUR,
  note='"Balkan SL", "Balkan MO SL", "BalkanMO SL" and "BMOSL" (2022 BMOSL, C1: the British BMO has no shortlist, so this is the Balkan one).')
C('JBMO', 'Junior Balkan Mathematical Olympiad', 'Europe (regional)', 'international', group=EUR)
C('JBMO_SL', 'Junior Balkan Mathematical Olympiad Shortlist', 'Europe (regional)', 'international', group=EUR)
C('RMM', 'Romanian Masters of Mathematics', 'International', 'international', group=INTL,
  note='Includes "Romanian MoM".')
C('RMM_SL', 'Romanian Masters of Mathematics Shortlist', 'International', 'international', group=INTL)
C('MEMO', 'Middle European Mathematical Olympiad', 'Europe (regional)', 'international', group=EUR)
C('BALTIC', 'Baltic Way', 'Europe (regional)', 'international', group=EUR)
C('BENELUX', 'Benelux Mathematical Olympiad', 'Europe (regional)', 'international', group=EUR)
C('NORDIC', 'Nordic Mathematical Contest', 'Europe (regional)', 'international', group=EUR)
C('TOT', 'Tournament of Towns', 'International', 'international', group=INTL)
C('IBERO', 'Iberoamerican Mathematical Olympiad', 'Latin America (regional)', 'international', group=LATAM)
C('CONOSUR', 'Cono Sur Mathematical Olympiad', 'Latin America (regional)', 'international', group=LATAM)
C('PAGMO', "Pan-American Girls' Mathematical Olympiad", 'Latin America (regional)', 'international', group=LATAM)
C('PAMO', 'Pan-African Mathematics Olympiad', 'Africa (regional)', 'international', group=AFR)
C('PAMO_SL', 'Pan-African Mathematics Olympiad Shortlist', 'Africa (regional)', 'international', group=AFR)
C('MEDIT', 'Mediterranean Mathematics Competition', 'Europe (regional)', 'international', group=EUR)
C('EMC', 'European Mathematical Cup', 'Europe (regional)', 'international', group=EUR,
  note='"EMC" is the European Mathematical Cup in the sheet\'s acronym list; rows carry Senior/Junior leagues.')
C('FRANCO', 'Francophone Mathematical Olympiad', 'International', 'international', group=EUR)
C('CAPS', 'Czech-Austrian-Polish-Slovak Match', 'Europe (regional)', 'international', 'medium', group=EUR,
  note='"CAPS-Match" = Czech-Austrian-Polish-Slovak Match (caps.ista.ac.at). Merged with the one "2019 Czech-Polish-Slovak" row, its predecessor. Not the bank\'s "Austrian-Polish Mathematics Competition" (a different, older contest).')
C('HUNISR', 'Hungary-Israel Binational Mathematical Competition', 'Europe (regional)', 'international', group=EUR)
C('IZHO', 'International Zhautykov Olympiad', 'Kazakhstan (international)', 'international', group=ASIA)
C('SILK', 'Silk Road Mathematics Competition', 'Asia (regional)', 'international', group=ASIA)
C('IOM', 'International Olympiad of Metropolises', 'International', 'international', group=INTL)
C('CMC', 'Cyberspace Mathematical Competition', 'International', 'international', 'medium', group=INTL,
  note='Best reading of "2020 CMC, P_ of 8": the MAA/AoPS online contest of July 2020 (8 problems over 2 days). Not the Canadian MO.')
C('IST_FRIENDLY', 'Iran-Singapore-Taiwan Friendly Competition', 'Asia (regional)', 'international', 'medium', group=ASIA,
  note='Merges "Iran-Singapore-Taiwan", "IND-IRN-SGP-TWN", "India-Iran-Singapore-Taiwan" and "Mongolia-Iran-Singapore-Taiwan" friendly contests (same pre-IMO friendly, partner countries vary by year).')
C('IND_IRN', 'India-Iran Friendly Competition', 'Asia (regional)', 'international', 'medium', group=ASIA)
C('IND_SGP', 'India-Singapore Friendly Contest', 'Asia (regional)', 'international', 'medium', group=ASIA)
C('ASHES', 'Mathematical Ashes', 'United Kingdom / Australia', 'TST', group='British Olympiads',
  note='UK v Australia practice exam at the joint pre-IMO camp; filed with the British group (the other side is Australia).')
C('F3', 'UK-Australia Pre-IMO Camp Exchange Paper', 'United Kingdom / Australia', 'TST', 'medium', group='British Olympiads',
  note='"AUS -> UNK F3" / "UNK -> AUS F3" / "2019 F3": the third training paper at the joint UK-Australia pre-IMO camp, each team setting one for the other (AMT and UK IMO reports). Direction (AUS->UNK = set by Australia) belongs in the subsource. "2019 F3" assumed to be the same paper.')
C('IGO', 'Iranian Geometry Olympiad', 'Iran', 'international',
  note='Advanced/Intermediate/Elementary levels go in the subsource.')
C('SHARYGIN', 'Sharygin Geometry Olympiad', 'Russia', 'national')

# ---------------- university ----------------
C('PUTNAM', 'William Lowell Putnam Mathematical Competition', 'United States', 'university', group=UNI)
C('IMC', 'International Mathematics Competition for University Students', 'International', 'university', group=UNI,
  note='Not the UK Intermediate Mathematical Challenge ("UK IMC", filed separately).')
C('ICMC', 'Imperial-Cambridge Mathematics Competition', 'United Kingdom', 'university', 'high', group=UNI,
  note='Ambiguous acronym (also Indiana Collegiate Mathematics Competition, a bank source). Every ICMC row with a link points to icmathscomp.org and rows have Round 1/Round 2, so all are Imperial. Called "Imperial College Mathematics Competition" until about 2021 (the sheet\'s acronym list uses that name); rounds go in the subsource.')
C('SMMC', 'Simon Marais Mathematics Competition', 'Australia (international)', 'university', group=UNI)
C('SCHWEITZER', 'Miklos Schweitzer Mathematical Competition', 'Hungary', 'university', 'high', group=UNI,
  bank='Miklos Schweitzer Competitions by GJ Szekely (same contest; that book covers 1962-1991, these rows are 1952 and 2020)',
  note='Could be filed under the bank source name instead.')
C('TRIPOS', 'Cambridge Mathematical Tripos', 'United Kingdom', 'university', 'high', group=UNI,
  bank='Cambridge Tripos (in the DB per earlier notes; not on the owner\'s list)',
  note='2 university exam questions (adapted). Map straight to the bank\'s "Cambridge Tripos".')
C('ICL_PLUS', 'ICL-plus (unidentified)', 'United Kingdom?', 'other', 'low', group=UNID,
  note='"2018 ICL-plus": unknown. Curator also posts ICMC problems, so perhaps an Imperial College London (ICL) problem set.')

# ---------------- United States ----------------
US = 'United States'
C('USAMO', 'United States of America Mathematical Olympiad', US, 'national')
C('USAJMO', 'United States of America Junior Mathematical Olympiad', US, 'national')
C('USA_TST', 'United States of America Team Selection Test', US, 'TST')
C('USA_TSTST', 'United States of America Team Selection Test Selection Test', US, 'TST')
C('USA_EGMO_TST', "United States of America Team Selection Test for the European Girls' Mathematical Olympiad", US, 'TST')
C('AIME', 'American Invitational Mathematics Examination', US, 'national', bank='AIME (748 rows)',
  note='AIME, AIME I and AIME II merged; I/II go in the subsource. The bank calls it "AIME", so either rename the bank source to the full name or file these under "AIME".')
C('AMC', 'American Mathematics Competitions', US, 'national', 'medium',
  note='AMC 10/12 (A/B, Fall/Spring) plus one 1981 AHSME, its predecessor. Paper (AMC 10A, AMC 12B...) goes in the subsource.')
C('USAMTS', 'United States of America Mathematical Talent Search', US, 'national')
C('HMMT', 'Harvard-MIT Mathematics Tournament', US, 'national', note='Includes the "Harvard-MIT GUTS contest" (the HMMT Guts round).')
C('HMIC', 'Harvard-MIT Invitational Competition', US, 'national')
C('PUMAC', 'Princeton University Mathematics Competition', US, 'national')
C('CHMMC', 'Caltech Harvey Mudd Mathematics Competition', US, 'national')
C('SMT', 'Stanford Math Tournament', US, 'national')
C('BAMO', 'Bay Area Mathematical Olympiad', US, 'national')
C('ARML', 'American Regions Mathematics League', US, 'national')
C('ELMO', 'ELMO Mathematical Olympiad', US, 'national', 'medium',
  note='Student-run olympiad at the US MOP camp. "ELMO" has no fixed expansion (historically "Experimental Lincoln Math Olympiad"), so no non-acronym name exists; pick a form.')
C('ELMO_SL', 'ELMO Mathematical Olympiad Shortlist', US, 'national', 'medium', note='See ELMO.')
C('PROBE', 'Nebraska Math Day PROBE II', US, 'national', 'medium',
  note='"UNL PROBE II": essay round of the University of Nebraska-Lincoln Math Day (PROBE = Problems Requiring Original and Brilliant Effort).')
C('USEMO', 'United States Ersatz Math Olympiad', US, 'community', 'high', group=ONLINE,
  note='Evan Chen\'s online olympiad. "USEMO East" (2026, 3 rows) is merged in at medium confidence (looks like a 2026 split of the same contest).')
C('NIMO', 'National Internet Math Olympiad', US, 'community', group=ONLINE)
C('OMO', 'Online Math Open', US, 'community', group=ONLINE)

# ---------------- United Kingdom / Ireland ----------------
UK = 'United Kingdom'
C('BMO1', 'British Mathematical Olympiad Round 1', UK, 'national',
  note='Includes "2021 British MO, P3 of 6" (6-problem paper = Round 1) and "BMO1 2009".')
C('BMO2', 'British Mathematical Olympiad Round 2', UK, 'national', note='Includes "British MO Round 2".')
C('UK_TST', 'United Kingdom Team Selection Test', UK, 'TST')
C('IMOK', 'Intermediate Mathematical Olympiad and Kangaroo', UK, 'national',
  note='UKMT IMOK olympiad papers: C = Cayley, H = Hamilton, M = Maclaurin (paper goes in the subsource). Includes "Maclaurin Olympiad" and "Cayley Olympiad".')
C('UK_JMO', 'UK Junior Mathematical Olympiad', UK, 'national')
C('UKMOG', 'UK Mathematical Olympiad for Girls', UK, 'national')
C('UK_SMC', 'UK Senior Mathematical Challenge', UK, 'national', note='"SMC"/"UK SMC"/"UKSMC"/"Senior Mathematical Challenge" (25-question UKMT paper; 2026 row links to ukmt.org.uk).')
C('UK_IMC', 'UK Intermediate Mathematical Challenge', UK, 'national')
C('UK_PINK', 'UK Pink Kangaroo', UK, 'national')
C('UK_STMC', 'UK Senior Team Maths Challenge', UK, 'national')
C('UK_TRAINING', 'UK IMO Team Training', UK, 'TST', 'low', note='"UK Training", no year or paper.')
C('IRMO', 'Irish Mathematical Olympiad', 'Ireland', 'national', note='"Irish MO" and "IrMO".')
C('IRL_EGMO_TST', "Irish Team Selection Test for the European Girls' Mathematical Olympiad", 'Ireland', 'TST')
C('IRL_TRAINING', 'Irish Mathematical Olympiad Training', 'Ireland', 'other', 'medium', note='"Irish MO Training Handout".')
C('MAYNOOTH', 'Maynooth University Mathematical Olympiad', 'Ireland', 'national', 'low',
  note='"2020 Maynooth Olympiad, P_ of 10": Maynooth runs Irish olympiad training; possibly the 2020 Irish MO or a Maynooth mock.')

# ---------------- Canada ----------------
CA = 'Canada'
C('CMO_CAN', 'Canadian Mathematical Olympiad', CA, 'national',
  note='Ambiguous acronym "CMO" (Canada or China). Every "CMO" row is "P_ of 5" (Canada has 5 problems, China 6) and the linked ones go to cms.math.ca, so all are Canadian. China\'s olympiad appears as "China MO"/"CNO"/"China National Olympiad".')
C('CJMO', 'Canadian Junior Mathematical Olympiad', CA, 'national', note='Linked rows go to cms.math.ca.')
C('CAN_BUFFET', 'Canadian Winter Camp Buffet Contest', CA, 'TST', 'medium')
C('EUCLID', 'Euclid Mathematics Contest', CA, 'national', note='University of Waterloo CEMC.')
C('PASCAL', 'Pascal Mathematics Contest', CA, 'national', 'medium',
  note='"2024 CMO, Pascal P20" is the Waterloo CEMC Pascal contest, not the Canadian MO.')
C('FERMAT', 'Fermat Mathematics Contest', CA, 'national', 'medium',
  note='"2024 CMO, Fermat P25" is the Waterloo CEMC Fermat contest, not the Canadian MO.')

# ---------------- China / HK / Taiwan ----------------
C('CHN_MO', 'China Mathematical Olympiad', 'China', 'national',
  note='"China MO", "China Mathematical Olympiad", "China National Olympiad" and "CNO" (the sheet\'s acronym list: Chinese National Olympiad).')
C('CHN_TST', 'China Team Selection Test', 'China', 'TST', note='"China TST", "China TST Test N", "China TST Day N", "China TST1" merged; test/day go in the subsource.')
C('CGMO', "China Girls' Mathematical Olympiad", 'China', 'national')
C('CWMI', 'China Western Mathematical Invitational', 'China', 'national', note='Merges "China Western MO"/"Mathematical Olympiad" (its former name).')
C('CHN_LEAGUE', 'China National High School Mathematics League', 'China', 'national', note='Includes "China Round 2" (the League\'s second round).')
C('CHKMO', 'China Hong Kong Mathematical Olympiad', 'Hong Kong', 'national')
C('HK_TST', 'Hong Kong Team Selection Test', 'Hong Kong', 'TST')
C('TWN_TST', 'Taiwan Team Selection Test', 'Taiwan', 'TST', note='Rounds, quizzes, independent studies and mock papers go in the subsource.')
C('TWN_MO', 'Taiwan Mathematical Olympiad', 'Taiwan', 'national')
C('IMOC', 'Taiwan IMOC Mathematical Olympiad', 'Taiwan', 'mock', 'medium',
  note='"Taiwan IMOC", "IMOC", "IMOCSL" (its shortlist). A Taiwanese olympiad-style contest run by former team members; expansion of IMOC not confirmed.')

# ---------------- other Asia ----------------
C('JPN_MO_FINAL', 'Japan Mathematical Olympiad Final Round', 'Japan', 'national')
C('JPN_MO_PRELIM', 'Japan Mathematical Olympiad Preliminary Round', 'Japan', 'national')
C('JPN_JMO', 'Japan Junior Mathematical Olympiad', 'Japan', 'national')
C('JPN_TST', 'Japan Team Selection Test', 'Japan', 'TST')
C('OMC', 'Online Math Contest (Japan)', 'Japan', 'community', 'medium', group=ONLINE, note='"OMC Beginner Contest NNN" (onlinemathcontest.com).')
C('KMO', 'Korean Mathematical Olympiad', 'South Korea', 'national', 'medium',
  note='"Korean MO", "Korea MO", "Korea National Olympiad", "Korea, Final Round", "FKMO" merged; round (incl. Final Round = FKMO) goes in the subsource.')
C('KJMO', 'Korean Junior Mathematical Olympiad', 'South Korea', 'national')
C('PRK_TST', 'North Korea Team Selection Test', 'North Korea', 'TST')
C('SGP_MO', 'Singapore Mathematical Olympiad', 'Singapore', 'national',
  note='Open/Senior/Junior sections (Round 2) merged; section goes in the subsource.')
C('SGP_TST', 'Singapore Team Selection Test', 'Singapore', 'TST')
C('SGP_JR_TRAIN', 'Singapore Junior Team Training', 'Singapore', 'TST', 'medium')
C('SGP_CWMI_TST', 'Singapore Team Selection Test for the China Western Mathematical Invitational', 'Singapore', 'TST')
C('MYS_TST', 'Malaysian Team Selection Tests', 'Malaysia', 'TST', 'medium',
  note='Merges Malaysia TST, IMO TST, APMO TST, Squad Selection Test and "IMO Malaysian Training Camp 1".')
C('MYS_JMO', 'Malaysia Junior Olympiad of Mathematics', 'Malaysia', 'national')
C('IDN_MO', 'Indonesian National Mathematics Olympiad', 'Indonesia', 'national', 'medium',
  note='"Indonesia MO" and "INAMO Round 1" (INAMO read as the Indonesian national olympiad, OSN).')
C('PHL_MO', 'Philippine Mathematical Olympiad', 'Philippines', 'national', note='Qualifying/Area/National stages and the National Oral round go in the subsource.')
C('THA_MO', 'Thailand Mathematical Olympiad', 'Thailand', 'national')
C('THA_TSTST', 'Thailand Team Selection Test Selection Test', 'Thailand', 'TST', 'medium')
C('THA_MOCK_IMO', 'Thailand Mock International Mathematical Olympiad', 'Thailand', 'TST', 'medium',
  note='Assumed to be the Thai IMO camp\'s mock (selection) paper rather than a community mock.')
C('VNM_MO', 'Vietnam Mathematical Olympiad', 'Vietnam', 'national')
C('VNM_TST', 'Vietnam Team Selection Test', 'Vietnam', 'TST')
C('INMO', 'Indian National Mathematical Olympiad', 'India', 'national')
C('RMO', 'Indian Regional Mathematical Olympiad', 'India', 'national', 'high',
  note='"RMO" = India\'s Regional MO: the 2018 row links to the HBCSE CRMO-2018 solutions; "India RMO" also present. Not Romanian (that is "Romanian MO").')
C('IND_TST', 'India Team Selection Test', 'India', 'TST', note='"India TST" and "Indian TST".')
C('IND_EGMO_TST', "India Team Selection Test for the European Girls' Mathematical Olympiad", 'India', 'TST', note='Includes "India EGMO TST Practice Test 2".')
C('IND_IMOTC', 'Indian International Mathematical Olympiad Training Camp', 'India', 'TST', 'medium',
  note='"INMOTC" (sheet\'s acronym list: Indian National Mathematical Olympiad Training Camp) and "India Practice Test" (camp practice tests).')
C('IOQM', 'Indian Olympiad Qualifier in Mathematics', 'India', 'national')
C('STEMS', 'STEMS Mathematics Olympiad (Chennai Mathematical Institute)', 'India', 'national', 'medium',
  note='"India STEMS Category A/B", the online olympiad run by Chennai Mathematical Institute students.')
C('BGD_MO', 'Bangladesh Mathematical Olympiad', 'Bangladesh', 'national')
C('NPL_TST', 'Nepal Team Selection Test', 'Nepal', 'TST')
C('IRN_TST', 'Iran Team Selection Test', 'Iran', 'TST')
C('IRN_MO', 'Iranian Mathematical Olympiad', 'Iran', 'national',
  note='Second/third rounds merged ("Iran MO", "Iranian MO", "Iran Round 2", "Iran MO 3rd Round"); "2005 Iran" and "Iran 1996" filed here at low confidence.')
C('IRN_COMB', 'Iranian Combinatorics Olympiad', 'Iran', 'national')
C('ISR_TST', 'Israel Team Selection Test', 'Israel', 'TST')
C('ISR_MO', 'Israel Mathematical Olympiad', 'Israel', 'national', 'medium',
  note='"Israel MO" (7-problem paper; probably the national/Gillis olympiad) and "Israel 3rd Round".')
C('GROSSMAN', 'Grossman Mathematical Olympiad', 'Israel', 'national', note='"Grosman"/"Grossman" spellings merged.')
C('ISR_REVENGE', 'Israel Olympic Revenge', 'Israel', 'TST', note='"Israel Olympic Revenge", "Israel Revenge" and its 2023 shortlist.')
C('ISR_IMC_TST', 'Israel Team Selection Test for the International Mathematics Competition', 'Israel', 'TST', 'low', note='"2021 Israel IMCTST".')
C('ISR_IMO_PRACTICE', 'Israel IMO Team Practice', 'Israel', 'TST', 'medium')
C('ISR_SPRING', 'Israel Spring Group Competition', 'Israel', 'national', 'medium')
C('ISR_CHAMP', 'Israel National Mathematics Championship', 'Israel', 'national', 'medium')
C('SAU_TST', 'Saudi Arabia Team Selection Tests', 'Saudi Arabia', 'TST', 'medium', note='IMO Training Test and Preselection Test merged.')
C('KAZ_MO', 'Kazakhstan National Mathematical Olympiad', 'Kazakhstan', 'national')
C('MNG_MO', 'Mongolian Mathematical Olympiad', 'Mongolia', 'national')
C('TUR_TST', 'Turkey Team Selection Test', 'Turkey', 'TST')
C('TUR_EGMO_TST', "Turkey Team Selection Test for the European Girls' Mathematical Olympiad", 'Turkey', 'TST')
C('TUR_JMO', 'Turkey Junior National Olympiad', 'Turkey', 'national')
C('ARM_MO', 'Armenian National Mathematical Olympiad', 'Armenia', 'national', 'medium', note='"Armenian National MO" and "Armenian Republican Olympiad".')
C('AZE_JMO', 'Azerbaijan Junior Mathematical Olympiad', 'Azerbaijan', 'national')

# ---------------- Europe ----------------
C('ALL_RUSSIAN', 'All-Russian Olympiad', 'Russia', 'national',
  note='"All-Russian MO", "All Russian MO", "ARMO", "Russia Round 4"; "1999 Russia" and "2023 Russia" filed here at low confidence.')
C('RUS_TST', 'Russia Team Selection Test', 'Russia', 'TST')
C('STPETE', 'Saint Petersburg Mathematical Olympiad', 'Russia', 'national',
  note='Same olympiad series as the old Leningrad MO (bank has "Grade Five Competition from the Leningrad Mathematical Olympiad", a different grade/book).')
C('R239', '239 School Mathematical Olympiad', 'Russia', 'national')
C('MOSCOW', 'Moscow Mathematical Olympiad', 'Russia', 'national')
C('MOSCOW_GEO', 'Moscow Oral Geometry Olympiad', 'Russia', 'national')
C('USSR', 'All-Union Mathematical Olympiad (USSR)', 'Soviet Union', 'national', group='Russian Olympiads')
C('UKR_MO', 'Ukrainian Mathematical Olympiad', 'Ukraine', 'national')
C('UKR_TST', 'Ukraine Team Selection Test', 'Ukraine', 'TST')
C('KYIV', 'Kyiv City Mathematical Olympiad', 'Ukraine', 'national')
C('BLR_MO', 'Belarusian Mathematical Olympiad', 'Belarus', 'national')
C('BLR_TST', 'Belarus Team Selection Test', 'Belarus', 'TST')
C('CHISINAU', 'Chisinau City Mathematical Olympiad', 'Moldova', 'national')
C('MDA_TST', 'Moldova Team Selection Test', 'Moldova', 'TST')
C('ROU_MO', 'Romanian National Mathematical Olympiad', 'Romania', 'national')
C('ROU_TST', 'Romania Team Selection Test', 'Romania', 'TST')
C('BGR_TST', 'Bulgaria Team Selection Test', 'Bulgaria', 'TST')
C('BGR_EGMO_TST', "Bulgaria Team Selection Test for the European Girls' Mathematical Olympiad", 'Bulgaria', 'TST')
C('KAZANLAK', 'Kazanlak Spring Mathematics Tournament', 'Bulgaria', 'national')
C('SOZOPOL', 'International Festival of Young Mathematicians Sozopol', 'Bulgaria', 'national', 'medium')
C('SRB_MO', 'Serbian Mathematical Olympiad', 'Serbia', 'national')
C('SRB_TST', 'Serbia Team Selection Test', 'Serbia', 'TST', note='Includes one "Serbia and Montenegro TST" (2005).')
C('YUG', 'Yugoslav Federal Mathematical Competition', 'Yugoslavia', 'national')
C('HRV_MO', 'Croatian Mathematical Olympiad', 'Croatia', 'national')
C('HRV_TST', 'Croatia Team Selection Test', 'Croatia', 'TST')
C('SVN_MO', 'Slovenian Mathematical Olympiad', 'Slovenia', 'national')
C('SVN_TST', 'Slovenia Team Selection Test', 'Slovenia', 'TST')
C('BIH_MO', 'Bosnia and Herzegovina Mathematical Olympiad', 'Bosnia and Herzegovina', 'national', 'medium')
C('KOS_MO', 'Kosovo Mathematical Olympiad', 'Kosovo', 'national')
C('ALB_MO', 'Albanian Mathematical Olympiad', 'Albania', 'national')
C('GRC_MO', 'Greek Mathematical Olympiad', 'Greece', 'national')
C('GRC_JBMO_TST', 'Greece Junior Balkan Team Selection Test', 'Greece', 'TST')
C('GRC_JMO', 'Greek Junior Mathematical Olympiad', 'Greece', 'national')
C('CYP_TST', 'Cyprus Team Selection Test', 'Cyprus', 'TST')
C('CYP_JBMO_TST', 'Cyprus Junior Balkan Team Selection Test', 'Cyprus', 'TST')
C('POL_MO', 'Polish Mathematical Olympiad', 'Poland', 'national')
C('POL_JMO', 'Polish Junior Mathematical Olympiad', 'Poland', 'national')
C('KURSCHAK', 'Kurschak Mathematics Competition', 'Hungary', 'national', 'high',
  bank='Hungarian Problem Books (same competition series; those books stop at 1963, this row is 1978)')
C('AUT_MO', 'Austrian Mathematical Olympiad', 'Austria', 'national',
  note='All rounds merged (Beginners\' Competition, Junior olympiad, Regional Competition, Final Round); round goes in the subsource. Not the bank\'s "Austrian-Polish Mathematics Competition".')
C('BWM', 'Bundeswettbewerb Mathematik', 'Germany', 'national', note='Includes "German Federal MC (34th)", the same contest in English.')
C('DEU_MO', 'German Mathematical Olympiad', 'Germany', 'national', 'medium',
  note='"German MO" (rounds 2-4/final), "Germany MO", "German National Olympiad" = the Mathematik-Olympiade. Some "German MO" rows without a round could be the Bundeswettbewerb.')
C('DEU_TST', 'Germany Team Selection Test', 'Germany', 'TST')
C('NLD_MO', 'Dutch Mathematical Olympiad', 'Netherlands', 'national', note='"Dutch MO", "Dutch MO final", "Netherlands MO", "Dutch MO, Second Round".')
C('NLD_TST', 'Dutch Team Selection Tests', 'Netherlands', 'TST', note='IMO TST, BxMO/EGMO TST and IMO TSTST papers merged.')
C('FLANDERS_MO', 'Flanders Mathematical Olympiad', 'Belgium', 'national')
C('FLANDERS_JMO', 'Flanders Junior Mathematical Olympiad', 'Belgium', 'national')
C('FRA_TST', 'France Team Selection Test', 'France', 'TST')
C('CHE_TST', 'Swiss Team Selection Test', 'Switzerland', 'TST')
C('CHE_FINAL', 'Swiss Mathematical Olympiad Final Round', 'Switzerland', 'national')
C('ITA_MO', 'Italian Mathematical Olympiad', 'Italy', 'national', note='"Italian MO", "ITAMO", "Italy MO".')
C('ITA_CAMP', 'Italian Senior Camp Admission Test', 'Italy', 'TST')
C('ITA_ARCHIMEDE', 'Giochi di Archimede', 'Italy', 'national')
C('ESP_MO', 'Spanish Mathematical Olympiad', 'Spain', 'national')
C('PRT_MO', 'Portuguese Mathematical Olympiad', 'Portugal', 'national')
C('FIN_MO', 'Finnish Mathematical Olympiad', 'Finland', 'national', note='"Finnish MO" and "Finnland MO".')
C('SWE_MO', 'Swedish Mathematical Olympiad', 'Sweden', 'national', note='"Sweden" (no year) filed here at low confidence.')
C('ABEL', 'Niels Henrik Abel Mathematics Contest', 'Norway', 'national', 'medium',
  note='Norway\'s national olympiad: "Niels Henrik Abel Contest" and "Norwegian MO" (Round 2/Finals) merged.')
C('LTU_BW_TST', 'Lithuanian Baltic Way Team Selection Test', 'Lithuania', 'TST')
C('LVA_BW_TST', 'Latvian Baltic Way Team Selection Test', 'Latvia', 'TST')

# ---------------- Latin America / Africa ----------------
C('MEX_MO', 'Mexican Mathematical Olympiad', 'Mexico', 'national')
C('BRA_MO', 'Brazilian Mathematical Olympiad', 'Brazil', 'national')
C('BRA_EGMO_TST', "Brazil Team Selection Test for the European Girls' Mathematical Olympiad", 'Brazil', 'TST')
C('BRA_REVENGE', 'Brazilian Olympic Revenge', 'Brazil', 'TST')
C('ARG_MO', 'Argentine Mathematical Olympiad', 'Argentina', 'national')
C('ARG_TST', 'Argentina Team Selection Test', 'Argentina', 'TST')
C('CHL_MO', 'Chilean Mathematical Olympiad', 'Chile', 'national', 'medium', note='Classification round and junior level merged.')
C('CRI_MO', 'Costa Rican Mathematical Olympiad', 'Costa Rica', 'national')
C('ECU_JMO', 'Ecuadorian Junior Mathematical Olympiad', 'Ecuador', 'national')
C('PRY_MO', 'Paraguayan Mathematical Olympiad', 'Paraguay', 'national')
C('ZAF_MO', 'South African Mathematics Olympiad', 'South Africa', 'national')
C('ZAF_TSTST', 'South Africa Team Selection Test Selection Test', 'South Africa', 'TST')
C('ZAF_CAMP', 'South African Olympiad Training Camp', 'South Africa', 'TST', 'medium')
C('MAR_MO', 'Moroccan National Mathematical Olympiad', 'Morocco', 'national')
C('NGA_JMO', 'Nigerian Junior Mathematics Olympiad', 'Nigeria', 'national')

# ---------------- Oceania ----------------
AU = 'Australia'
C('AUS_MO', 'Australian Mathematical Olympiad', AU, 'national',
  note='Ambiguous acronym "AMO" (Australian vs Austrian etc.). Every "AMO, P_ of 8" row fits Australia (8 problems over 2 days; linked rows go to amt.edu.au). "2021 AMO P4/P5" (no "of 8") filed here at medium confidence.')
C('AUS_SENIOR', 'Australian Mathematical Olympiad Committee Senior Contest', AU, 'national', 'high',
  note='Ambiguous acronym "ASC": the 2020 rows link to the UWA SMC2020 paper, so ASC = (AMOC) Australian Senior Contest; merged with "AMOC Senior Contest".')
C('AUS_AIMO', 'Australian Intermediate Mathematics Olympiad', AU, 'national')
C('AUS_TST', 'Australian Team Selection Test', AU, 'TST', note='"Some Australian TST" (no year) filed here at low confidence.')
C('AUS_TRAINING', 'Australian Mathematical Olympiad Committee Training', AU, 'TST', 'medium',
  note='"Australian Training Tournament" and "AMOC School of Excellence".')
C('WA_GEO', 'West Australian Geometry Olympiad', AU, 'other', 'low', note='No year; not identified.')
NZ = 'New Zealand'
C('NZMO1', 'New Zealand Mathematical Olympiad Round 1', NZ, 'national', note='"NZMO1", "New Zealand MO Round 1".')
C('NZMO2', 'New Zealand Mathematical Olympiad Round 2', NZ, 'national', note='"NZMO2", "NZMO R2", "New Zealand MO Round 2"; "2019 New Zealand MO" (no round) filed here at low confidence.')
C('NZ_CAMP_SEL', 'New Zealand Camp Selection Problems', NZ, 'TST', 'medium',
  note='"NZ Camp Selection (Problems/Test)", "New Zealand Camp Selection Problems"; "2014 NZMO, P_ of 10" filed here (pre-2019 there was no NZMO; the 10-problem take-home was the camp selection set).')
C('NZ_SQUAD', 'New Zealand Squad Selection Test', NZ, 'TST')
C('NZ_SMC', 'New Zealand Senior Mathematics Competition', NZ, 'national', note='"NZ SMC", "NZ Senior Math(s) Comp(etition)", "New Zealand Senior MC".')
C('NZ_MMW', 'New Zealand Monday Maths Workshop', NZ, 'other', 'medium')
C('NZ_CAMP', 'New Zealand IMO Camp Problem Sets', NZ, 'TST', 'medium', note='"NZIMO Camp PS2".')

# ---------------- Math Olympiad Discord Server ----------------
C('MODS_ATTR', MODS, 'Online', 'community', 'high', group=MODS,
  note='Owner rule: "Folklore", "Original", "Unknown" go here. Proposed: also named classics/theorems, folklore puns ("Lore", "F01K10R3" = FOLKLORE, "Typo"), personal attributions and loose web sources. Keep the original label as the subsource.')
C('MODSMO', 'Math Olympiad Discord Server Mathematical Olympiad', 'Online', 'community', 'high', group=MODS,
  note='MODS = the server\'s own contest; Round 2 and Intermediate goes in the subsource.')
C('MODS_GEO', 'Math Olympiad Discord Server Geometry Contest', 'Online', 'community', group=MODS)
C('MODS_INTER', 'Math Olympiad Discord Server Intermediate Contest', 'Online', 'community', group=MODS, note='"MODS Intermediate Contest" and "MODSMO Intermediate".')
C('MODS_BEGIN', 'Math Olympiad Discord Server Beginner Contest', 'Online', 'community', group=MODS)
C('AFMO', "Math Olympiad Discord Server April Fools' Olympiad", 'Online', 'community', 'medium', group=MODS,
  note='"AFMO": every row is dated 1 April and one note says it was posted as an April Fools\' joke source, so read as the server\'s own April Fools MO.')

# ---------------- mocks ----------------
C('DIMO', 'DEMO Mock International Mathematical Olympiad', 'Online', 'mock', 'high', group=MOCK, note='Sheet\'s acronym list: "IMO mock by DEMO group".')
C('DAMO', 'DEMO Mock United States of America Mathematical Olympiad', 'Online', 'mock', 'high', group=MOCK, note='Sheet\'s acronym list: "USAMO mock by DEMO group".')
C('GIMO', 'GIMO Mock Olympiad', 'Online', 'mock', 'low', group=MOCK, note='Expansion unknown; 6-problem paper, same curator as DIMO.')
C('XOOK', 'XOOK Mock Olympiad', 'Online', 'mock', 'low', group=MOCK, note='Expansion unknown; AoPS-posted 6-problem mock (2023, 2025).')
C('LMAO', 'LMAO Mock Olympiad', 'Online', 'mock', 'medium', group=MOCK, note='AoPS mock with a shortlist (LMAO SL 2021); expansion unknown. Includes "LMAO Revenge".')
C('CAMO', 'Christmas American Mathematical Olympiad', 'Online', 'mock', 'medium', group=MOCK,
  note='"CAMO" (AoPS wiki lists it under Christmas Math Competitions) merged with "2021 Christmas American Math Olympiad".')
C('XMAS_JMO', 'Christmas Junior Mathematical Olympiad', 'Online', 'mock', 'medium', group=MOCK)
C('XMAS_MOCK', 'Christmas Mock Olympiad', 'Online', 'mock', 'low', group=MOCK)
C('XMAS_GEO', 'Christmas Special Mock Geometry Olympiad', 'Online', 'mock', group=MOCK)
C('IGMO', 'IGMO Mock Olympiad', 'Online', 'mock', 'low', group=MOCK, note='Round 1, qualification, shortlist and Christmas edition merged; expansion unknown.')
C('AGO', "Amateur Geometer's Olympiad", 'Online', 'mock', 'high', group=MOCK,
  note='"AGO", "Amateurs Geometry Olympiad", "1st Amateur\'s Geometry Olympiad": one community geometry contest (founder atavic, also a curator here); categories go in the subsource.')
C('MGO', 'Mocktest Geometry Olympiad', 'Online', 'mock', group=MOCK)
C('FAKE_USAMO', 'Fake United States of America Mathematical Olympiad', 'Online', 'mock', 'medium', group=MOCK)
C('REAL_IMOSL', '"Real IMO Shortlist" Mock', 'Online', 'mock', 'low', group=MOCK, note='"2018 Real IMOSL": not the official 2018 shortlist (G6 differs); joke/mock collection.')
C('LEAKED_RMM', '"Leaked RMM" Mock', 'Online', 'mock', 'low', group=MOCK, note='"2019 Leaked RMM": joke/mock paper, not the official RMM.')
C('OTIS_AIME', 'OTIS Mock American Invitational Mathematics Examination', 'Online', 'mock', group=MOCK)
C('AOPS_AMC', 'AoPS Practice American Mathematics Competition 12', 'Online', 'mock', group=MOCK)
C('NICE', 'NICE Mock Contest', 'Online', 'mock', 'low', group=MOCK, note='25-question AMC-style mock; expansion unknown.')
C('MOCK_INAMO', 'Mock Indonesian National Mathematics Olympiad', 'Online', 'mock', 'medium', group=MOCK)
C('IFEO', 'International Functional Equations Olympiad', 'Online', 'mock', 'medium', group=MOCK, note='AoPS link slug "international_fe_olympiad"; includes its shortlist.')
C('SEIF', 'SEIF Mock Olympiad', 'Online', 'mock', 'low', group=MOCK, note='Includes "SEIF SL"/"SEIFSL"; expansion unknown.')
C('GOTEEM', 'GOTEEM Mock Geometry Olympiad', 'Online', 'mock', 'low', group=MOCK)
C('T4MO', 'T4MO Mock Olympiad', 'Online', 'mock', 'low', group=MOCK)
C('CCCCC', 'CCCCC Mock Contest', 'Online', 'mock', 'low', group=MOCK, note='Note says "AoPS contest link".')
C('POGCHAMP', 'POGCHAMP Mock Olympiad', 'Online', 'mock', 'low', group=MOCK)
C('GGG4', 'GGG4 Mock Geometry Contest', 'Online', 'mock', 'low', group=MOCK)
C('SYMO', 'SYMO Mock Olympiad', 'Online', 'mock', 'low', group=MOCK)
C('MEOW', 'MEOW Mock Olympiad', 'Online', 'mock', 'medium', group=MOCK)
C('PGMO', 'PGMO Mock Olympiad', 'Online', 'mock', 'low', group=MOCK)
C('APRIL_MO', 'April Mock Olympiad', 'Online', 'mock', 'low', group=MOCK)
C('LAIN', 'Lain Mock Olympiad', 'Online', 'mock', 'low', group=MOCK)
C('BLISH', '"Blish" Summer Competition', 'Online', 'mock', 'low', group=MOCK)
C('GOWACA', 'Geometry Olympiad Without A Cool Acronym', 'Online', 'mock', group=MOCK)
C('BOUNTY', 'Geometry 1 Problem Bounty Hunt Contest', 'Online', 'mock', 'medium', group=MOCK)
C('INFTY_MO', 'Infinity Mock Olympiad', 'Online', 'mock', 'low', group=MOCK, note='Source cell is mojibake of something like "∞•MO".')
C('IMSC', 'International Mathematical Summer Camp', 'Online?', 'mock', 'low', group=MOCK,
  note='"IMSC" (and "Stronger 2024 IMSC"): a 2025 IMSC paper is titled International Mathematical Summer Camp; not confirmed for these rows.')

# ---------------- online community ----------------
C('OPENPOTD', 'OpenPOTD Duels', 'Online', 'community', 'medium', group=ONLINE)
C('SOLVEFIRE', 'Solvefire Contests', 'Online', 'community', 'low', group=ONLINE)
C('DISCORD_SMP', 'Discord SMP Competition', 'Online', 'community', 'low', group=ONLINE)
C('DGGMATHS', 'DGGMaths Riddles', 'Online', 'community', 'medium', group=ONLINE, note='Weekly riddle sets (Discord attachments); 9 rows across weeks.')
C('GEOLYMPIAD', 'Geolympiad', 'Online', 'community', group=ONLINE)
C('DGO', 'DGO Geometry Olympiad (Team Round)', 'Online', 'community', 'low', group=ONLINE,
  note='Ambiguous acronym "DGO": every row is "DGO Team" geometry (2022-23), one linked to a Discord attachment, others to AoPS; expansion not found.')
C('ATHEMATH', 'Athemath Camp Application Problems', 'Online', 'other', 'medium', group=ONLINE)
C('G2CAMP', 'G2 Math Camp Application Problems', 'Online', 'other', 'medium', group=ONLINE)

# ---------------- unidentified ----------------
C('FIST', 'FIST (unidentified)', '?', 'other', 'low', group=UNID, note='"1977 FIST", "1990 FIST": a historical contest; acronym not identified.')
C('EMO', 'EMO (unidentified)', '?', 'other', 'low', group=UNID, note='"2026 EMO, P4 of 4": could be the Emirates MO or a mock; not identified.')
C('SMO', 'SMO (unidentified)', '?', 'other', 'low', group=UNID, note='"2020 SMO, P1 of 6": not Singapore (5-problem papers) on its face; could be Serbian/Swiss/Saudi MO or a mock.')
C('AMM', 'AMM (unidentified)', '?', 'other', 'low', group=UNID, note='"2026 AMM, P_ of 5" (4 rows, AoPS user blog link): not the American Mathematical Monthly (no paper of 5); likely a 2026 mock.')
C('MIST', 'MIST (unidentified)', '?', 'other', 'low', group=UNID)
C('IMBT', 'IMBT (unidentified)', '?', 'other', 'low', group=UNID, note='"2026 IMBT, Day 3, P4 of 8".')
C('LOTUS', 'Lotus Olympiad', '?', 'other', 'low', group=UNID)
C('CENTENNIAL', 'Centennial Schools Mathematics Competition', '?', 'other', 'low', group=UNID, note='Spelled "Centenial" in the sheet.')
C('OLIMATO', 'OliMaTo', '?', 'other', 'low', group=UNID)
C('SAUNA', 'Sauna Final Round', '?', 'other', 'low', group=UNID)
C('LUMAT', 'LuMaT', '?', 'other', 'low', group=UNID, note='"LuMaT 2018 Pre-eliminary Round".')
C('SHARP', 'Sharp Calculator Competition', '?', 'other', 'low', group=UNID)

# ---------------- books / journals / websites ----------------
C('PST', 'Di Pasquale, Do and Mathews\' Problem Solving Tactics', 'Book', 'book', 'high', group=BOOKS,
  note='"PST" (sheet\'s acronym list: Problem Solving Tactics, AMT, 2015; authors Angelo Di Pasquale, Norman Do, Daniel Mathews).')
C('ACPS', "Zeitz's The Art and Craft of Problem Solving", 'Book', 'book', 'high', group=BOOKS,
  note='"ACPS", the spelled-out title, "The coin game (ACPS, ...)" and "1995 Russia (ACPS 7.1.32)" (a Russian 1995 problem quoted in the book).')
C('PEN', "Lee's Problems in Elementary Number Theory", 'Book', 'book', 'medium', group=BOOKS, note='"PEN" (Hojoo Lee et al., online problem collection).')
C('GEO110', "Andreescu and Pohoata's 110 Geometry Problems for the International Mathematical Olympiad", 'Book', 'book', 'medium', group=BOOKS)
C('SIERP250', "Sierpinski's 250 Problems in Elementary Number Theory", 'Book', 'book', 'high', group=BOOKS)
C('LEADER', "Leader's Introductory Problems", 'Book', 'book', 'low', group=BOOKS, note='"Introductory Problems" by Imre Leader (problem sheet/handout).')
C('MOT', "Andreescu and Enescu's Mathematical Olympiad Treasures", 'Book', 'book', 'medium', group=BOOKS)
C('WINKLER', "Winkler's Mathematical Puzzles", 'Book', 'book', 'low', group=BOOKS,
  bank='possibly (a Winkler 2024 PDF was an in-app source; check the bank label)', note='"Mathematical Puzzles", no author given.')
C('SOBERON', "Soberon's Problem-Solving Methods in Combinatorics", 'Book', 'book', 'medium', group=BOOKS)
C('PRASOLOV', "Prasolov's Problems in Plane and Solid Geometry", 'Book', 'book', 'medium', group=BOOKS, note='Includes "Praslov Problem 2.88" (misspelling).')
C('SETTHEORY', 'Problems in Set Theory (author unknown)', 'Book', 'book', 'low', group=BOOKS)
C('PFTB', "Andreescu and Dospinescu's Problems from the Book", 'Book', 'book', 'high', group=BOOKS)
C('ENGEL', "Engel's Problem-Solving Strategies", 'Book', 'book', 'medium', group=BOOKS, note='"PSS, Chapter 2, P27".')
C('MONT', "Khurmi's Modern Olympiad Number Theory", 'Book', 'book', 'medium', group=BOOKS, note='"MONT 4.9.10".')
C('GOLBERG', "Golberg's Olympiad Handout", 'Book', 'book', 'low', group=BOOKS, note='"Handout by Oleg Golberg".')
C('COFFEE', "Bollobas's The Art of Mathematics: Coffee Time in Memphis", 'Book', 'book', 'medium', group=BOOKS)
C('KOMAL', 'KoMaL (Kozepiskolai Matematikai es Fizikai Lapok)', 'Hungary (journal)', 'book', 'high', group=BOOKS, note='Problem numbers (A.715 etc.) go in the subsource.')
C('CRUX', 'Crux Mathematicorum', 'Canada (journal)', 'book', 'high', group=BOOKS)
C('KVANT', 'Kvant', 'Russia (journal)', 'book', 'medium', group=BOOKS)
C('MATHREFL', 'Mathematical Reflections', 'United States (journal)', 'book', 'high', group=BOOKS)
C('HDIGH', 'how-did-i-get-here.com', 'Website', 'book', 'medium', group=BOOKS, note='Sheet\'s acronym list: HDIGH = how-did-i-get-here.com (numbered problem archive).')

C('OTIS_ANTI', "Chen's OTIS Anti-Problems", 'Website', 'book', 'medium', group=BOOKS, note='Evan Chen OTIS handout.')

# ---------------- exams / programming (skip?) ----------------
C('CIE', 'Cambridge International A Level Mathematics 9709', 'United Kingdom', 'other', 'high', group=EXAMS, note='SKIP? school exam paper.')
C('HKDSE', 'Hong Kong Diploma of Secondary Education Mathematics', 'Hong Kong', 'other', 'high', group=EXAMS, note='SKIP? school exam paper.')
C('SMCC', "St. Mary's Canossian College Form 4 Final Exam", 'Hong Kong', 'other', 'high', group=EXAMS, note='SKIP? school exam paper.')
C('SOF', 'Science Olympiad Foundation International Mathematics Olympiad (sample paper)', 'India', 'other', 'high', group=EXAMS,
  note='SKIP? SOF "IMO" is a school-level MCQ test, not the International Mathematical Olympiad.')
C('GAOKAO', 'Gaokao (Chinese National College Entrance Examination)', 'China', 'other', 'high', group=EXAMS, note='SKIP? admission exam.')
C('KYOTO', 'Kyoto University Entrance Examination', 'Japan', 'other', 'high', group=EXAMS, note='SKIP? admission exam.')
C('UI_ENTRANCE', 'University of Indonesia Entrance Examination', 'Indonesia', 'other', 'high', group=EXAMS, note='SKIP? admission exam.')
C('HANOI', 'Hanoi Grade 10 Entrance Examination', 'Vietnam', 'other', 'high', group=EXAMS, note='SKIP? admission exam.')
C('ISI', 'Indian Statistical Institute Entrance Examination', 'India', 'other', 'high', group=EXAMS, note='SKIP? admission exam (olympiad-style subjective paper; could be kept).')
C('STEP', 'Sixth Term Examination Paper', 'United Kingdom', 'other', 'high', group=EXAMS, note='SKIP? admission exam (could be kept; proof-style).')
C('CODEFORCES', 'Codeforces', 'Online', 'other', 'high', group=PROG, note='SKIP? programming problems.')
C('USACO', 'USA Computing Olympiad', US, 'other', 'high', group=PROG, note='SKIP? programming olympiad.')
C('EULER', 'Project Euler', 'Online', 'other', 'high', group=PROG, note='SKIP? programming problems.')
C('IOI', 'International Olympiad in Informatics', 'International', 'other', 'high', group=PROG, note='SKIP? programming olympiad (row is adapted to a math problem; could be kept).')

SKIP_GROUPS = {EXAMS, PROG}
