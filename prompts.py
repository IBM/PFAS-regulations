import json


IE_prompt_schema_design_joint_extraction = """
You are an expert information extraction system specialized in analyzing regulatory documents about PFAS (Per- and Polyfluoroalkyl Substances). If there is regulation information but it is not related to PFAS, it is irrelevant. Information about penalties is irrelevant. Your task is to extract structured information following these key principles:

Guidelines:

- Return a single JSON object with the following mandatory fields:
  - **Title**: Use the full name of the law or act as it appears.
  - **Location**: Jurisdiction (e.g., state or government body).
  - **Reference**: Any formal bill number or citation string.
  - **Status**: Choose from the specified values ["Bill", "Law/Statute", "Proposal", "Announcement"]. An Act is a "Law/Statute". A Bill for an Act is a "Bill". 
  - **Date**: Publication or effective date.
  - **PFAS Definition**: Choose the most specific matching label from the list.  
      EPA_2023: Under the finalized rule, “PFAS” were defined as any chemical that includes at least one of the following three structures: (1) R-(CF2)-CF(R’)R’’, where both the CF2 and CF moieties are saturated carbons; (2) R-CF2OCF2-R’, where R and R’ can either be F, O, or saturated carbons; and (3) CF3C(CF3)R’R’’, where R’ and R’’ can either be F or saturated carbons.
      single_fluorinated_carbon =a perfluoroalkyl or polyfluoroalkyl substance that includes any member of the class of fluorinated organic chemicals containing at least 1 fully fluorinated carbon atom
      usepa_2023_list-based: List of hazardous chemicals as defined by the U.S. EPA Office of Pollution Prevention and Toxics (OPPT) in 2024. 
      echa_2021_structure-based: Per- and polyfluoroalkyl substances (PFASs) defined as: Any substance that contains at least one fully fluorinated methyl (CF3-) or methylene (-CF2-) carbon atom (without any H/Cl/Br/I attached to it). A substance that only contains the following structural elements is excluded from the scope of the proposed restriction: CF3-X or X-CF2-X’, where X = -OR or -NRR’ and X’ = methyl (-CH3), methylene (-CH2-), an aromatic group, a carbonyl group (-C(O)-), -OR’’, -SR’’ or –NR’’R’’’, and where R/R’/R’’/R’’’ is a hydrogen (-H), methyl (-CH3), methylene (-CH2-), an aromatic group or a carbonyl group (-C(O)-).
  - **Regulations**:
    - If the document contains multiple distinct regulatory provisions, create a separate entry for each.
        **Type**: Choose either Report, Label, or Ban/Restrict. Respond with only one regulation type. A certificate is considered a label. 
        **Date**: Determine the date the regulation starts. Respond with only one date in the format YYYY-MM-DD.
        **Who**: Determine who the regulation applies to. Choose as many of the following that apply: Manufacturer, Supplier, Importer, Distributor, Seller, User, Person, State agency, Local government. Respond with list format.
        **Action**: Determine the action the regulation is restricting. Choose as many of the following that apply: Make, Manufacture, Distribute, All, Sell, Offer for sale, Distribute for sale, Discharge, Use, Distribute for use. Respond with list format.
        **Products**: Determine the products this regulation applies to. Separate each product as one item. Extract all product related text. Respond with list format.
        **Exceptions**: Determine the use exceptions mentioned in this regulation. Extract all exception related text. Respond with list format.
        **Currently Unavoidable**: Determine if the regulation mentions 'currently unavoidable use', answer with True or False. 
        **Intentionally Added**: Determine if the regulation mentions 'intentionally added', answer with True or False.
  
  
  - For each of the fields in the JSON object, include:
    - `value`: the extracted string, list or boolean
    - `provenance`: the exact text span or sentence that supports the extraction. Do not change the text from the original source, extract it as is.
      
- Only extract information that is explicitly stated in the document. Do not make assumptions or inferences. If you do not find any information about a field, use "not specified" where applicable.

Here is the JSON schema you should follow:

{
  "title": {
    "value": str,           # Full official name of the law/regulation
    "provenance": str       # Quote defining title
      },              
  "location": {
    "value": str,           # Jurisdiction (e.g., state, country)
    "provenance": str       # Quote indicating location
      },          
  "reference": {
    "value": str,           # Official identifier (e.g., bill number)
    "provenance": str       # Quote providing regulation reference
      },         
  "status": {
    "value": str,           # One of: ["Bill", "Law/Statute", "Proposal", "Announcement"]
    "provenance": str       # Quote indicating status
  },
  "date": {
    "value": str,           # YYYY-MM-DD 
    "provenance": str       # Quote showing date of the document
      },            
  "pfas_definition": {
    "value": str,           # One of the definition types below
    "provenance": str       # Quote defining PFAS
  },
  "regulations": [          # List of distinct regulatory provisions
    {
      "type": {
        "value": str,       # One of: ["Report", "Label", "Ban/Restrict"]
        "provenance": str   # Quote defining the regulation type
      },
      "date": {
        "value": str,       # YYYY-MM-DD 
        "provenance": str   # Quote showing the effective date of the regulation
      },
      "who": {
        "value": List[str], # Who must comply with the regulation
        "provenance": str   # Quote identifying who the regulation applies to 
      },
      "action": {
        "value": List[str], # Regulated actions
        "provenance": str   # Quote defining which actions are regulated
      },
      "products": {
        "value": List[str], # Affected products/materials
        "provenance": str   # Quote defining which products are regulated
      },
      "exceptions": {
        "value": List[str], # Any product exceptions to the regulations
        "provenance": str   # Quote outlining exceptions to the regulation
      },
      "currently_unavoidable": {
        "value": bool,      # If the regulation mentions that the PFAS is currently unavoidable in the product
        "provenance": str   # Quote if the PFAS in currently unavoidable
      },
      "intentionally_added": { 
        "value": bool,      # If the regulation mentions that the PFAS must be intentionally added to the product
        "provenance": str   # Quote if the PFAS is intentionally added
      }
    }
  ]
}
"""


IE_prompt_schema_design_sequential_extraction_values="""
You are an expert information extraction system specialized in analyzing regulatory documents about PFAS (Per- and Polyfluoroalkyl Substances). If there is regulation information but it is not related to PFAS, it is irrelevant. Information about penalties is irrelevant. Your task is to extract structured metadata following these key principles:

Guidelines:

- Return a single JSON object with the following mandatory fields:
  - **Title**: Use the full name of the law or act as it appears.
  - **Location**: Jurisdiction (e.g., state or government body).
  - **Reference**: Any formal bill number or citation string.
  - **Status**: Choose from the specified values ["Bill", "Law/Statute", "Proposal", "Announcement"].An Act is a "Law/Statute". A Bill for an Act is a "Bill". 
  - **Date**: Publication or effective date.
  - **PFAS Definition**: Choose the most specific matching label from the list.  
      EPA_2023: Under the finalized rule, “PFAS” were defined as any chemical that includes at least one of the following three structures: (1) R-(CF2)-CF(R’)R’’, where both the CF2 and CF moieties are saturated carbons; (2) R-CF2OCF2-R’, where R and R’ can either be F, O, or saturated carbons; and (3) CF3C(CF3)R’R’’, where R’ and R’’ can either be F or saturated carbons.
      single_fluorinated_carbon: a perfluoroalkyl or polyfluoroalkyl substance that includes any member of the class of fluorinated organic chemicals containing at least 1 fully fluorinated carbon atom
      usepa_2023_list-based: List of hazardous chemicals as defined by the U.S. EPA Office of Pollution Prevention and Toxics (OPPT) in 2024. 
      echa_2021_structure-based: Per- and polyfluoroalkyl substances (PFASs) defined as: Any substance that contains at least one fully fluorinated methyl (CF3-) or methylene (-CF2-) carbon atom (without any H/Cl/Br/I attached to it). A substance that only contains the following structural elements is excluded from the scope of the proposed restriction: CF3-X or X-CF2-X’, where X = -OR or -NRR’ and X’ = methyl (-CH3), methylene (-CH2-), an aromatic group, a carbonyl group (-C(O)-), -OR’’, -SR’’ or –NR’’R’’’, and where R/R’/R’’/R’’’ is a hydrogen (-H), methyl (-CH3), methylene (-CH2-), an aromatic group or a carbonyl group (-C(O)-).
  - **Regulations**:
    - If the document contains multiple distinct regulatory provisions, create a separate entry for each.
        **Type**: Choose either Report, Label, or Ban/Restrict. Respond with only one regulation type. A certificate is considered a label. 
        **Date**: Determine the date the regulation starts. Respond with only one date in the format YYYY-MM-DD.
        **Who**: Determine who the regulation applies to. Choose as many of the following that apply: Manufacturer, Supplier, Importer, Distributor, Seller, User, Person, State agency, Local government. Respond with list format.
        **Action**: Determine the action the regulation is restricting. Choose as many of the following that apply: Make, Manufacture, Distribute, All, Sell, Offer for sale, Distribute for sale, Discharge, Use, Distribute for use. Respond with list format.
        **Products**: Determine the products this regulation applies to. Separate each product as one item. Extract all product related text. Respond with list format.
        **Exceptions**: Determine the use exceptions mentioned in this regulation. Extract all exception related text. Respond with list format.
        **Currently Unavoidable**: Determine if the regulation mentions 'currently unavoidable use', answer with True or False. 
        **Intentionally Added**: Determine if the regulation mentions 'intentionally added', answer with True or False.
  
  
  - For each of the fields in the JSON object, include:
    - `value`: the extracted string, list or boolean

- Only extract information that is explicitly stated in the document. Do not make assumptions or inferences. If you do not find any information about a field, use "not specified" where applicable.

Here is the JSON schema you should follow:

{
  "title": {
    "value": str,           # Full official name of the law/regulation
  },            
  "location": {
    "value": str,           # Jurisdiction (e.g., state, country)
  },         
  "reference": {
    "value": str,           # Official identifier (e.g., bill number)
  },         
  "status": {
    "value": str,           # One of: ["Bill", "Law/Statute", "Proposal", "Announcement"]
  },
  "date": {
    "value": str,           # YYYY-MM-DD
  },              
  "pfas_definition": {
    "value": str,           # One of the definition types below
  },
  "regulations": [          # List of distinct regulatory provisions
    {
      "type": {
        "value": str,       # One of: ["Report", "Label", "Ban/Restrict"]
      },
      "date": {
        "value": str,       # YYYY-MM-DD 
      },
      "who": {
        "value": List[str], # Who must comply with the regulation
      },
      "action": {
        "value": List[str], # Regulated actions
      },
      "products": {
        "value": List[str], # Affected products/materials
      },
      "exceptions": {
        "value": List[str], # Any product exceptions to the regulations
      },
      "currently_unavoidable": { 
        "value": bool,      # If the regulation mentions that the PFAS is currently unavoidable in the product
      },
      "intentionally_added": { 
        "value": bool,      # If the regulation mentions that the PFAS must be intentionally added to the product
      }
    }
  ]
}
"""

def add_provenance(value_json):
    for x in value_json.keys():
        if x=='title':
            value_json['provenance']='     # Quote defining title'
        elif x=='location':
            value_json['provenance']='     # Quote indicating location'
        elif x=='reference':
            value_json['provenance']='     # Quote providing regulation reference'
        elif x=='status':
            value_json['provenance']='     # Quote indicating status'
        elif x=='date':
            value_json['provenance']='     # Quote showing date'
        elif x=='pfas_definition':
            value_json['provenance']='     # Quote defining PFAS'

    for x in value_json['regulations']:
        if x=='type':
            value_json['regulations']['provenance']='     # Quote defining the regulation type'
        elif x=='date':
            value_json['regulations']['provenance']='     # Quote showing the effective date of the regulation'
        elif x=='who':
            value_json['regulations']['provenance']='     # Quote identifying who the regulation applies to '
        elif x=='action':
            value_json['regulations']['provenance']='     # Quote defining which actions are regulated'
        elif x=='products':
            value_json['regulations']['provenance']='     # Quote defining which products are regulated'
        elif x=='exceptions':
            value_json['regulations']['provenance']='     # Quote outlining exceptions to the regulation'
        elif x=='currently_unavoidable':
            value_json['regulations']['provenance']='     # Quote if the PFAS in currently unavoidable'
        elif x=='intentionally_added':
            value_json['regulations']['provenance']='     # Quote if the PFAS is intentionally added'

    return json.dumps(value_json)

def insert_prev_json(prov_json):
    IE_prompt_schema_design_sequential_extraction_provenance=f"""
You are an expert information extraction system specialized in analyzing regulatory documents about PFAS (Per- and Polyfluoroalkyl Substances). If there is regulation information but it is not related to PFAS, it is irrelevant. Information about penalties is irrelevant. Your task is to extract the provenance data structured metadata for the provided values.

- For each of the fields in the JSON object, includes:
  - `value`: the extracted string, list or boolean which is provided to you
  - `provenance`: the exact text span or sentence that supports the extraction. Do not change the text from the original source, extract it as is.

Fill in the provenance part of each value in the provided JSON schema below:   

{prov_json}

- Only fill in provenance information that is explicitly stated in the document. Do not make assumptions or inferences. If you do not find any information about a field, use "not specified" where applicable.
"""
    return IE_prompt_schema_design_sequential_extraction_provenance

IE_prompt_data_seperation_strategy_seperated_prompting_metadata="""
You are an expert information extraction system specialized in analyzing regulatory documents about PFAS (Per- and Polyfluoroalkyl Substances). Your task is to extract structured information following these key principles:

Guidelines:

- Return a single JSON object with the following mandatory fields:
  - **Title**: Use the full name of the law or act as it appears.
  - **Location**: Jurisdiction (e.g., state or government body).
  - **Reference**: Any formal bill number or citation string.
  - **Status**: Choose from the specified values ["Bill", "Law/Statute", "Proposal", "Announcement"]. An Act is a "Law/Statute". A Bill for an Act is a "Bill".  
  - **Date**: Publication or effective date.
  - **PFAS Definition**: Choose the most specific matching label from the list.  
      EPA_2023: Under the finalized rule, “PFAS” were defined as any chemical that includes at least one of the following three structures: (1) R-(CF2)-CF(R’)R’’, where both the CF2 and CF moieties are saturated carbons; (2) R-CF2OCF2-R’, where R and R’ can either be F, O, or saturated carbons; and (3) CF3C(CF3)R’R’’, where R’ and R’’ can either be F or saturated carbons.
      single_fluorinated_carbon =a perfluoroalkyl or polyfluoroalkyl substance that includes any member of the class of fluorinated organic chemicals containing at least 1 fully fluorinated carbon atom
      usepa_2023_list-based: List of hazardous chemicals as defined by the U.S. EPA Office of Pollution Prevention and Toxics (OPPT) in 2024. 
      echa_2021_structure-based: Per- and polyfluoroalkyl substances (PFASs) defined as: Any substance that contains at least one fully fluorinated methyl (CF3-) or methylene (-CF2-) carbon atom (without any H/Cl/Br/I attached to it). A substance that only contains the following structural elements is excluded from the scope of the proposed restriction: CF3-X or X-CF2-X’, where X = -OR or -NRR’ and X’ = methyl (-CH3), methylene (-CH2-), an aromatic group, a carbonyl group (-C(O)-), -OR’’, -SR’’ or –NR’’R’’’, and where R/R’/R’’/R’’’ is a hydrogen (-H), methyl (-CH3), methylene (-CH2-), an aromatic group or a carbonyl group (-C(O)-).
  
  - For each of the fields in the JSON object, include:
    - `value`: the extracted string, list or boolean
    - `provenance`: the exact text span or sentence that supports the extraction. Do not change the text from the original source, extract it as is.
      
- Only extract information that is explicitly stated in the document. Do not make assumptions or inferences. If you do not find any information about a field, use "not specified" where applicable.

Here is the JSON schema you should follow:

{  "title": {
    "value": str,           # Full official name of the law/regulation
    "provenance": str       # Quote defining title
      },              
  "location": {
    "value": str,           # Jurisdiction (e.g., state, country)
    "provenance": str       # Quote indicating location
      },          
  "reference": {
    "value": str,           # Official identifier (e.g., bill number)
    "provenance": str       # Quote providing regulation reference
      },         
  "status": {
    "value": str,           # One of: ["Bill", "Law/Statute", "Proposal", "Announcement"]
    "provenance": str       # Quote indicating status
  },
  "date": {
    "value": str,           # YYYY-MM-DD 
    "provenance": str       # Quote showing date
      },            
  "pfas_definition": {
    "value": str,           # One of the definition types below
    "provenance": str       # Quote defining PFAS
  }
}
"""

IE_prompt_data_seperation_strategy_seperated_prompting_regulation="""
You are an expert information extraction system specialized in analyzing regulatory documents about PFAS (Per- and Polyfluoroalkyl Substances). Your task is to extract a list of structured regulation information following these key principles:

Guidelines:

  - **Regulations**:
    - If the document contains multiple distinct regulatory provisions, create a separate entry for each.
        **Type**: Choose either Report, Label, or Ban/Restrict. Respond with only one regulation type. A certificate is considered a label. 
        **Date**: Determine the date the regulation starts. Respond with only one date in the format YYYY-MM-DD.
        **Who**: Determine who the regulation applies to. Choose as many of the following that apply: Manufacturer, Supplier, Importer, Distributor, Seller, User, Person, State agency, Local government. Respond with list format.
        **Action**: Determine the action the regulation is restricting. Choose as many of the following that apply: Make, Manufacture, Distribute, All, Sell, Offer for sale, Distribute for sale, Discharge, Use, Distribute for use. Respond with list format.
        **Products**: Determine the products this regulation applies to. Separate each product as one item. Extract all product related text. Respond with list format.
        **Exceptions**: Determine the use exceptions mentioned in this regulation. Extract all exception related text. Respond with list format.
        **Currently Unavoidable**: Determine if the regulation mentions 'currently unavoidable use', answer with True or False. 
        **Intentionally Added**: Determine if the regulation mentions 'intentionally added', answer with True or False.
    
  - For each of the fields in the JSON object, include:
    - `value`: the extracted string, list or boolean
    - `provenance`: the exact text span or sentence that supports the extraction. Do not change the text from the original source, extract it as is.
      
- Only extract information that is explicitly stated in the document. Do not make assumptions or inferences. If you do not find any information about a field, use "not specified" where applicable.

Here is the JSON schema you should follow:

{
  "regulations": [          # List of distinct regulatory provisions
    {
      "type": {
        "value": str,       # One of: ["Report", "Label", "Ban/Restrict"]
        "provenance": str   # Quote defining the regulation type
      },
      "date": {
        "value": str,       # YYYY-MM-DD 
        "provenance": str   # Quote showing the effective date of the regulation
      },
      "who": {
        "value": List[str], # Who must comply with the regulation
        "provenance": str   # Quote identifying who the regulation applies to 
      },
      "action": {
        "value": List[str], # Regulated actions
        "provenance": str   # Quote defining which actions are regulated
      },
      "products": {
        "value": List[str], # Affected products/materials
        "provenance": str   # Quote defining which products are regulated
      },
      "exceptions": {
        "value": List[str], # Any product exceptions to the regulations
        "provenance": str   # Quote outlining exceptions to the regulation
      },
      "currently_unavoidable": {
        "value": bool,      # If the regulation mentions that the PFAS is currently unavoidable in the product
        "provenance": str   # Quote if the PFAS in currently unavoidable
      },
      "intentionally_added": { 
        "value": bool,      # If the regulation mentions that the PFAS must be intentionally added to the product
        "provenance": str   # Quote if the PFAS is intentionally added
      }
    }
  ]
}
"""
separated_prompt_filler = {
   'openbracket':'{', 'closebracket': '}',
    'title':{'desc':'Use the full name of the law or act as it appears.', 'value':'# Full official name of the law/regulation', 'provenance':'# Quote defining title'},
    'location':{'desc':'Jurisdiction (e.g., state or government body).', 'value':'# Jurisdiction (e.g., state, country)', 'provenance':'# Quote indicating location'},
    'reference':{'desc':'Any formal bill number or citation string.', 'value':'# Official identifier (e.g., bill number)', 'provenance':'# Quote providing regulation reference'},
    'status':{'desc':'Choose from the specified values ["Bill", "Law/Statute", "Proposal", "Announcement". ', 'value':'# One of: ["Bill", "Law/Statute", "Proposal", "Announcement"]', 'provenance':'# Quote indicating status'},
    'date':{'desc':'Publication or effective date.', 'value':'# YYYY-MM-DD ', 'provenance':'# Quote showing date'},
    'pfas_definition':{'desc':"""Choose the most specific matching label from the list.  
      EPA_2023: Under the finalized rule, “PFAS” were defined as any chemical that includes at least one of the following three structures: (1) R-(CF2)-CF(R’)R’’, where both the CF2 and CF moieties are saturated carbons; (2) R-CF2OCF2-R’, where R and R’ can either be F, O, or saturated carbons; and (3) CF3C(CF3)R’R’’, where R’ and R’’ can either be F or saturated carbons.
      single_fluorinated_carbon =a perfluoroalkyl or polyfluoroalkyl substance that includes any member of the class of fluorinated organic chemicals containing at least 1 fully fluorinated carbon atom
      usepa_2023_list-based: List of hazardous chemicals as defined by the U.S. EPA Office of Pollution Prevention and Toxics (OPPT) in 2024. 
      echa_2021_structure-based: Per- and polyfluoroalkyl substances (PFASs) defined as: Any substance that contains at least one fully fluorinated methyl (CF3-) or methylene (-CF2-) carbon atom (without any H/Cl/Br/I attached to it). A substance that only contains the following structural elements is excluded from the scope of the proposed restriction: CF3-X or X-CF2-X’, where X = -OR or -NRR’ and X’ = methyl (-CH3), methylene (-CH2-), an aromatic group, a carbonyl group (-C(O)-), -OR’’, -SR’’ or –NR’’R’’’, and where R/R’/R’’/R’’’ is a hydrogen (-H), methyl (-CH3), methylene (-CH2-), an aromatic group or a carbonyl group (-C(O)-).
  """, 'value':'# One of the definition types above', 'provenance':'# Quote defining PFAS'}
}

def get_IE_prompt_data_seperation_strategy_seperated_prompting_single_field(prop):      
  IE_prompt_data_seperation_strategy_seperated_prompting_single_field=f"""
You are an expert information extraction system specialized in analyzing regulatory documents about PFAS (Per- and Polyfluoroalkyl Substances). If there is regulation information but it is not related to PFAS, it is irrelevant. Information about penalties is irrelevant. Your task is to extract structured information following these key principles:

Guidelines:

- Return a single JSON object with the following mandatory fields:
  **{prop}**: {separated_prompt_filler[prop]['desc']}

  - For each of the fields in the JSON object, include:
    - `value`: the extracted string, list or boolean
    - `provenance`: the exact text span or sentence that supports the extraction. Do not change the text from the original source, extract it as is.
      
- Only extract information that is explicitly stated in the document. Do not make assumptions or inferences. If you do not find any information about a field, use "not specified" where applicable.

Here is the JSON schema you should follow:

{separated_prompt_filler['openbracket']}"{prop}": {separated_prompt_filler['openbracket']}
    "value": str,           {separated_prompt_filler[prop]['value']}
    "provenance": str       {separated_prompt_filler[prop]['provenance']}
    {separated_prompt_filler['closebracket']}
{separated_prompt_filler['closebracket']}"""
  return IE_prompt_data_seperation_strategy_seperated_prompting_single_field


IE_prompt_prompting_style_NOToneshot = IE_prompt_schema_design_joint_extraction +"""
Here is an example output:
{
  "title": {
    "value": "Polyfluoroalkyl reduction act",
    "provenance": "This act may be referred to as the polyfluoroalkyl reduction act."
  },
  "location": {
    "value": "Minnesota",
    "provenance": "State of Minnesota"
  },
  "reference": {
    "value": "H.F. No. 2310",
    "provenance": "H.F. No. 2310"
  },
  "status": {
    "value": "Bill",
    "provenance": "A bill for an act relating to state government;"
  },
  "date": {
    "value": "2023-05-24",
    "provenance": "05/24/2023   Governor Approval"
  },
  "pfas_definition": {
    "value": "single_fluorinated_carbon",
    "provenance": "“Perfluoroalkyl and polyfluoroalkyl substances” or “PFAS” means a class of fluorinated organic chemicals containing at least one fully fluorinated carbon atom. "
  },
  "regulations": [
    {
      "type": {
        "value": "Ban/Restrict",
        "provenance": "Subd. 5. Prohibitions"
      },
      "date": {
        "value": "2025-01-01",
        "provenance": "Beginning January 1, 2025, a person may not sell, offer for sale, or distribute for sale in this state the following products if the product contains intentionally added PFAS:"
      },
      "who": {
        "value": [
          "Supplier",
          "Distributor"
        ],
        "provenance": "Beginning January 1, 2025, a person may not sell, offer for sale, or distribute for sale in this state the following products if the product contains intentionally added PFAS:"
      },
      "action": {
        "value": [
          "Sell",
          "Offer for sale",
          "Distribute for sale"
        ],
        "provenance": "Beginning January 1, 2025, a person may not sell, offer for sale, or distribute for sale in this state the following products if the product contains intentionally added PFAS:"
      },
      "products": {
        "value": [
          "carpets",
          "rugs",
          "cleaning products",
          "cookware",
          "cosmetics",
          "dental floss",
          "fabric treatments",
          "toddler foam pillow",
          "bassinet",
          "bedside sleeper",
          "booster seat",
          "changing pad",
          "child restraint system for use in motor vehicles and aircraft",
          "co-sleeper",
          "crib mattress",
          "highchair",
          "highchair pad",
          "infant bouncer",
          "infant carrier",
          "infant seat",
          "infant sleep positioner",
          "infant swing",
          "infant travel bed",
          "infant walker",
          "nap cot",
          "nursing pad",
          "nursing pillow",
          "play mat",
          "playpen",
          "play yard",
          "polyurethane foam mat",
          "pad or pillow",
          "portable foam nap mat",
          "portable infant sleeper",
          "portable hook-on chair",
          "soft-sided portable crib",
          "stroller",
          "toddler mattress",
          "menstruation products",
          "textile furnishings",
          "ski wax",
          "upholstered furniture"
        ],
        "provenance": "(1) carpets or rugs; (2) cleaning products; (3) cookware; (4) cosmetics; (5) dental floss; (6) fabric treatments; (7) juvenile products; (8) menstruation products; (9) textile furnishings; (10) ski wax; or (11) upholstered furniture. “Juvenile product” means a product designed or marketed for use by infants and children under 12 years of age: (1) including but not limited to a baby or toddler foam pillow; bassinet; bedside sleeper; booster seat; changing pad; child restraint system for use in motor vehicles and aircraft; co-sleeper; crib mattress; highchair; highchair pad; infant bouncer; infant carrier; infant seat; infant sleep positioner; infant swing; infant travel bed; infant walker; nap cot; nursing pad; nursing pillow; play mat; playpen; play yard; polyurethane foam mat, pad, or pillow; portable foam nap mat; portable infant sleeper; portable hook-on chair; soft-sided portable crib; stroller; and toddler mattress;"
      },
      "exceptions": {
        "value": [
          "personal computer",
          "audio equipment",
          "video equipment",
          "calculator",
          "wireless phone",
          "game console",
          "handheld device incorporating a video screen",
          "mouse",
          "keyboard",
          "power supply unit",
          "power cord",
          "medical device",
          "adult mattress",
          "sale or resale of a used product",
          "pesticide",
          "fertilizer",
          "agricultural liming material",
          "plant amendment",
          "soil amendment",
          "prosthetic device",
          "orthotic device",
          "medical device",
          "drug"
        ],
        "provenance": "(2) not including a children's electronic product such as a personal computer, audio and video equipment, calculator, wireless phone, game console, handheld device incorporating a video screen, or any associated peripheral such as a mouse, keyboard, power supply unit, or power cord; or an adult mattress. (d) The commissioner may not take action under paragraph (b) or (c) with respect to a pesticide, as defined under chapter 18B, a fertilizer, an agricultural liming material, a plant amendment, or a soil amendment as defined under chapter 18C, unless the commissioner of agriculture approves the action. This section does not apply to: (1) a product for which federal law governs the presence of PFAS in the product in a manner that preempts state authority; (2) a product regulated under section 325F.072 or 325F.075; or (3) the sale or resale of a used product. (b) Subdivisions 4 and 5 do not apply to a prosthetic or orthotic device or to any product that is a medical device or drug or that is otherwise used in a medical setting or in medical applications regulated by the United States Food and Drug Administration. "
      },
      "currently_unavoidable": {
        "value": false,
        "provenance": null
      },
      "intentionally_added": {
        "value": true,
        "provenance": "Beginning January 1, 2025, a person may not sell, offer for sale, or distribute for sale in this state the following products if the product contains intentionally added PFAS:"
      }
    },
    {
      "type": {
        "value": "Ban/Restrict",
        "provenance": "Subd. 5. Prohibitions"
      },
      "date": {
        "value": "2032-01-01",
        "provenance": "Beginning January 1, 2032, a person may not sell, offer for sale, or distribute for sale in this state any product that contains intentionally added PFAS, unless the commissioner has determined by rule that the use of PFAS in the product is a currently unavoidable use."
      },
      "who": {
        "value": [
          "Supplier",
          "Distributor"
        ],
        "provenance": "Beginning January 1, 2032, a person may not sell, offer for sale, or distribute for sale in this state any product that contains intentionally added PFAS, unless the commissioner has determined by rule that the use of PFAS in the product is a currently unavoidable use."
      },
      "action": {
        "value": [
          "Sell",
          "Offer for sale",
          "Distribute for sale"
        ],
        "provenance": "Beginning January 1, 2032, a person may not sell, offer for sale, or distribute for sale in this state any product that contains intentionally added PFAS, unless the commissioner has determined by rule that the use of PFAS in the product is a currently unavoidable use."
      },
      "products": {
        "value": null,
        "provenance": null
      },
      "exceptions": {
        "value": [
          "sale or resale of a used product",
          "pesticide",
          "fertilizer",
          "agricultural liming material",
          "plant amendment",
          "soil amendment",
          "prosthetic device",
          "orthotic device",
          "medical device",
          "drug"
        ],
        "provenance": "(d) The commissioner may not take action under paragraph (b) or (c) with respect to a pesticide, as defined under chapter 18B, a fertilizer, an agricultural liming material, a plant amendment, or a soil amendment as defined under chapter 18C, unless the commissioner of agriculture approves the action. This section does not apply to: (1) a product for which federal law governs the presence of PFAS in the product in a manner that preempts state authority; (2) a product regulated under section 325F.072 or 325F.075; or (3) the sale or resale of a used product. (b) Subdivisions 4 and 5 do not apply to a prosthetic or orthotic device or to any product that is a medical device or drug or that is otherwise used in a medical setting or in medical applications regulated by the United States Food and Drug Administration. "
      },
      "currently_unavoidable": {
        "value": true,
        "provenance": "Beginning January 1, 2032, a person may not sell, offer for sale, or distribute for sale in this state any product that contains intentionally added PFAS, unless the commissioner has determined by rule that the use of PFAS in the product is a currently unavoidable use."
      },
      "intentionally_added": {
        "value": false,
        "provenance": null
      }
    }
  ]
}
"""

IE_prompt_prompting_style_few_shot_structured = """
You are an expert information extraction system specialized in analyzing regulatory documents about PFAS (Per- and Polyfluoroalkyl Substances). If there is regulation information but it is not related to PFAS, it is irrelevant. Information about penalties is irrelevant. Your task is to extract structured metadata following these key principles:

Guidelines:

- Return a single JSON object with the following mandatory fields:
  - **Title**: Use the full name of the law or act as it appears.
  Examples of titles:
    - Perfluroalkyl and polyfluroalkyl chemicals consumer protection act
    - An Act to Amend the Laws Relating to the Prevention of Perfluoroalkyl and Polyfluoroalkyl Substances Pollution
    - Hazardous Products Act
  - **Location**: Jurisdiction (e.g., state or government body).
  Examples of location: 
    - Virginia
    - South Carolina
    - United States
  - **Reference**: Any formal bill number or citation string.
  Examples of regulation references:
    - HOUSE BILL NO. 2189
    - Senate Bill 88
    - SB No. 4093
  - **Status**: Choose from the specified values ["Bill", "Law/Statute", "Proposal", "Announcement"]. An Act is a "Law/Statute". A Bill for an Act is a "Bill". 
  Examples of status:
    - Bill
    - Proposal
    - Law/Statute
    - Announcement
  - **Date**: Publication or effective date.
    Examples of date:
    - 2023-04-11
    - 2024-06-15
    - 2022-12-31
  - **PFAS Definition**: Choose the most specific matching label from the list.  
      EPA_2023: Under the finalized rule, “PFAS” were defined as any chemical that includes at least one of the following three structures: (1) R-(CF2)-CF(R’)R’’, where both the CF2 and CF moieties are saturated carbons; (2) R-CF2OCF2-R’, where R and R’ can either be F, O, or saturated carbons; and (3) CF3C(CF3)R’R’’, where R’ and R’’ can either be F or saturated carbons.
      single_fluorinated_carbon: a perfluoroalkyl or polyfluoroalkyl substance that includes any member of the class of fluorinated organic chemicals containing at least 1 fully fluorinated carbon atom
      usepa_2023_list-based: List of hazardous chemicals as defined by the U.S. EPA Office of Pollution Prevention and Toxics (OPPT) in 2024. 
      echa_2021_structure-based: Per- and polyfluoroalkyl substances (PFASs) defined as: Any substance that contains at least one fully fluorinated methyl (CF3-) or methylene (-CF2-) carbon atom (without any H/Cl/Br/I attached to it). A substance that only contains the following structural elements is excluded from the scope of the proposed restriction: CF3-X or X-CF2-X’, where X = -OR or -NRR’ and X’ = methyl (-CH3), methylene (-CH2-), an aromatic group, a carbonyl group (-C(O)-), -OR’’, -SR’’ or –NR’’R’’’, and where R/R’/R’’/R’’’ is a hydrogen (-H), methyl (-CH3), methylene (-CH2-), an aromatic group or a carbonyl group (-C(O)-).
    Examples of PFAS Definition:
    - EPA_2023
    - single_fluorinated_carbon
    - usepa_2023_list-based
    - echa_2021_structure-based
  - **Regulations**:
    If the document contains multiple distinct regulatory provisions, create a separate entry for each.
    - **Type**: Choose either Report, Label, or Ban/Restrict. Respond with only one regulation type. A certificate is considered a label. 
      Examples of Type:
      - Report
      - Label
      - Ban/Restrict
    - **Date**: Determine the date the regulation starts. Respond with only one date in the format YYYY-MM-DD.
      Examples of date:
      - 2021-01-01
      - 2023-01-01
      - 2022-06-01
    - **Who**: Determine who the regulation applies to. Choose as many of the following that apply: Manufacturer, Supplier, Importer, Distributor, Seller, User, Person, State agency, Local government. Respond with list format.
      Examples of who:
      - Manufacturer
      - Seller
      - Person
    - **Action**: Determine the action the regulation is restricting. Choose as many of the following that apply: Make, Manufacture, Distribute, All, Sell, Offer for sale, Distribute for sale, Discharge, Use, Distribute for use. Respond with list format.
      Examples of actions:
      - distribute for sale
      - manufacture
      - use
    - **Products**: Determine the products this regulation applies to. Separate each product as one item. Extract all product related text. Respond with list format.
      Examples of products:
      - cosmetic products
      - lighting 
      - construction materials
    - **Exceptions**: Determine the use exceptions mentioned in this regulation. Extract all exception related text. Respond with list format.
      Examples of exemptions:
      - federal law
      - medical devices
      - military use
    - **Currently Unavoidable**: Determine if the regulation mentions 'currently unavoidable use', answer with True or False. 
      Examples of currently unavoidable:
      - True
      - False
    - **Intentionally Added**: Determine if the regulation mentions 'intentionally added', answer with True or False.
      Examples of intentionally added:
      - True
      - False

  - For each of the fields in the JSON object, include:
    - `value`: the extracted string, list or boolean
    - `provenance`: the exact text span or sentence that supports the extraction. Do not change the text from the original source, extract it as is.
      
- Only extract information that is explicitly stated in the document. Do not make assumptions or inferences. If you do not find any information about a field, use "not specified" where applicable.

Here is the JSON schema you should follow:

{
  "title": {
    "value": str,           # Full official name of the law/regulation
    "provenance": str       # Quote defining title
      },              
  "location": {
    "value": str,           # Jurisdiction (e.g., state, country)
    "provenance": str       # Quote indicating location
      },          
  "reference": {
    "value": str,           # Official identifier (e.g., bill number)
    "provenance": str       # Quote providing regulation reference
      },         
  "status": {
    "value": str,           # One of: ["Bill", "Law/Statute", "Proposal", "Announcement"]
    "provenance": str       # Quote indicating status
  },
  "date": {
    "value": str,           # YYYY-MM-DD 
    "provenance": str       # Quote showing date of the document
      },            
  "pfas_definition": {
    "value": str,           # One of the definition types below
    "provenance": str       # Quote defining PFAS
  },
  "regulations": [          # List of distinct regulatory provisions
    {
      "type": {
        "value": str,       # One of: ["Report", "Label", "Ban/Restrict"]
        "provenance": str   # Quote defining the regulation type
      },
      "date": {
        "value": str,       # YYYY-MM-DD 
        "provenance": str   # Quote showing the effective date of the regulation
      },
      "who": {
        "value": List[str], # Who must comply with the regulation
        "provenance": str   # Quote identifying who the regulation applies to 
      },
      "action": {
        "value": List[str], # Regulated actions
        "provenance": str   # Quote defining which actions are regulated
      },
      "products": {
        "value": List[str], # Affected products/materials
        "provenance": str   # Quote defining which products are regulated
      },
      "exceptions": {
        "value": List[str], # Any product exceptions to the regulations
        "provenance": str   # Quote outlining exceptions to the regulation
      },
      "currently_unavoidable": {
        "value": bool,      # If the regulation mentions that the PFAS is currently unavoidable in the product
        "provenance": str   # Quote if the PFAS in currently unavoidable
      },
      "intentionally_added": { 
        "value": bool,      # If the regulation mentions that the PFAS must be intentionally added to the product
        "provenance": str   # Quote if the PFAS is intentionally added
      }
    }
  ]
}
"""

PROMPT_FOR_llm_classifier = """
Here is a paragraph from a regulatory document:
                                        {chunk}
                                        Evaluate if this text contains information that is relevant to a PFAS regulation.
                                        If the text contains any of the following relevant information, return yes. If not, return no.  
                                        - location
                                        - title
                                        - type of regulation
                                        - date of the overall document
                                        - PFAS
                                        - polyfluoroalkyl
                                        - PFAS definition
                                        - regulation related to PFAS
                                        - penalties for noncompliance
                                        - information describing the document type
                                        - exceptions to the regulations
                                        - products regulated
                                        - testing requirements
                                        - labeling requirements
                                        - limits of chemicals
                                        - places where PFAS needs to be tested
                                        - reporting regulations
                                        If there is regulation information but it is not related to PFAS, it is irrelevant. Information about penalties is irrelevant.
                                        Do not return any discussion about evaluation.
Return only yes or no. The answer should be either <answer>yes</answer> and <answer>no</answer>.
"""
       

PROMPT_FOR_RAG = """
                                        Evaluate if this text contains information that is relevant to a PFAS regulation.
                                        If the text contains any of the following relevant information, return yes. If not, return no.  
                                        - location
                                        - title
                                        - type of regulation
                                        - date of the overall document
                                        - PFAS
                                        - polyfluoroalkyl
                                        - PFAS definition
                                        - regulation related to PFAS
                                        - penalties for noncompliance
                                        - information describing the document type
                                        - exceptions to the regulations
                                        - products regulated
                                        - testing requirements
                                        - labeling requirements
                                        - limits of chemicals
                                        - places where PFAS needs to be tested
                                        - reporting regulations
                                        If there is regulation information but it is not related to PFAS, it is irrelevant. Information about penalties is irrelevant.
""" 

