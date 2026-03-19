import os
import json

# --- CONFIGURATION ---
# don't touch language packs!
TARGET_DIRECTORY = r"C:\git\SCED-downloads\decomposed\scenario"

# --- MAPPING DATA ---
UPDATE_MAP = {
    "01125": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/15880137107443680826/1D59B455D33AE69AC93E14AEE419016C86FE4392/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/9427387790762012200/5D18065D4AE7B679A37B4142BFAAA25F4932503E/",
    },
    "01126": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/15079866707997651761/1A035888F740DFF25C9104211570304F9BFC03ED/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/14908098894486900142/790C3BA63BA48C1EE7FA9BA00A0E8C3C70ED4FF7/",
    },
    "01127": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/15079866707997651761/1A035888F740DFF25C9104211570304F9BFC03ED/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/12403197278035522562/070DA2BBBAFE2FB3990D065D77716DEE5608B345/",
    },
    "01128": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/11310584181517286233/B5A8A69BE14B34F9EF3086A9B1A94D45C858FFCD/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/10343506166725622090/07E1937B7DB1556EF9AE0452BAF9FDE42E8017E0/",
    },
    "01129": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/12423702360779241744/AE927954BF806B09116745640249DC9D7D2F1402/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/10909145057120250562/EF7756AB8B37DD855E9753892CCFD1A4651987FF/",
    },
    "01130": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/12391068993312609883/794726CEC5B3756D1B5D3E3BE0E7F25561A47D16/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/15638983872463623053/22974A3846D5A015F4AE9C7400A71C713E3D3339/",
    },
    "01131": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/12391068993312609883/794726CEC5B3756D1B5D3E3BE0E7F25561A47D16/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/10313752965353424707/B28B1361449F617FBBEC6B7D3458ECE5B398F5E1/",
    },
    "01132": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/11432955743395386026/FC8C14BB1F8DB4CCE60514824D931E603ACDFDD9/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/12939569091458373917/A57AE9C70B5FB0C4FD9A29FE4DB6BC9E24F45EF7/",
    },
    "01134": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/12936548610804325764/97E6DA0BEC90BAD15DB3CCFF01526E4F4E887877/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/11361932330769021535/DD9C538898F769D7B702A9D7058CE8D051C92C22/",
    },
    "01150": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/12720769756818830739/002769C6B909E0DB2EFA55AB74C5FE59E9F21BB4/",
    },
    "01151": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/13986487507349416364/9CD326D87082F0F129BDD43CF6D9D0E4E2AEF5FB/",
    },
    "01152": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/14447960433674793788/6303F2083BF80B5C3BB04372CFEAD28B6CDE91AA/",
    },
    "01153": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/12203572110956570723/5501008E281E4104CC4EAE06871F0C5CCA417443/",
    },
    "01154": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/11608495261644552048/2D924A6C5F0F8CEA6861A456A621BECF5AD4F9A2/",
    },
    "01155": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/15002012580281891917/C1B2C0FA4360007F36DC99707E3A240D9BE4666E/",
    },
    "50027": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/12391068993312609883/794726CEC5B3756D1B5D3E3BE0E7F25561A47D16/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/17069649008338435964/62635A48E20471D3F643787FED8A13FC85424980/",
    },
    "50028": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/12936548610804325764/97E6DA0BEC90BAD15DB3CCFF01526E4F4E887877/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/9745034279007361672/459F057696808F21E9474113821517EC9FF8DC87/",
    },
    "50029": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/12423702360779241744/AE927954BF806B09116745640249DC9D7D2F1402/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/15799085821702995561/F6005C0A61F01E4039D2EDC7C65F88C09780FB69/",
    },
    "50030": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/15880137107443680826/1D59B455D33AE69AC93E14AEE419016C86FE4392/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/16152432624879908203/F566F89A2D5DCF56928C5B12C7A110934140E4E2/",
    },
    "50033": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/16544115579536030550/DE91DA7472ECDD7656AA5831D4C42D15D2986FB3/",
    },
    "50034": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/15949951138733915164/E9749127991387E2871485FEE673E20C0D873F66/",
    },
    "50035": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/10666587778667776850/34ED8964E4873D48CCBC9225EE8D7163B29AC62F/",
    },
    "50036": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/12489840583873292728/7B6A1DE259CD18B4EDFF6AD8EB22E6FE8BB1D1E9/",
    },
    "54021": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/12697698724705489305/916EBE38B0DD51943B754767EF5B7CA4FB409751/",
    },
    "54022": {
        "face": "https://steamusercontent-a.akamaihd.net/ugc/10039895077102366513/A4B27CFD64422A1055CA9DBE662A366D9FCA200F/",
        "back": "https://steamusercontent-a.akamaihd.net/ugc/9466813440081341621/3FAFA2163E3E2005F32D14262AB1DAFD22B5295C/",
    },
}


def update_json_data(data, index):
    prefix = str(int(index))
    data["CardID"] = int(f"{prefix}00")
    data["CustomDeck"] = {
        prefix: {
            "BackIsHidden": True,
            "BackURL": UPDATE_MAP[index]["back"],
            "FaceURL": UPDATE_MAP[index]["face"],
            "NumHeight": 1,
            "NumWidth": 1,
            "Type": 0,
        }
    }
    data["Name"] = "Card"  # custom card
    return data


def process_json_files():
    processed_count = 0
    last_output_count = 0
    match_count = 0

    for root, dirs, files in os.walk(TARGET_DIRECTORY):
        for file in files:
            if not file.lower().endswith(".json"):
                continue

            processed_count += 1

            if processed_count > (last_output_count + 500):
                last_output_count = processed_count
                print(
                    f"Progress: Scanned {processed_count} files, updated {match_count} files."
                )

            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Skipping {file}: Error reading JSON ({e})")
                continue

            # Check for GMNotes or GMNotes_path
            gm_notes_raw = None

            if data.get("GMNotes"):
                gm_notes_raw = data["GMNotes"]
            elif data.get("GMNotes_path"):
                # Construct path to the .gmnotes file
                base_path = os.path.splitext(file_path)[0]
                gm_notes_file = base_path + ".gmnotes"

                if os.path.exists(gm_notes_file):
                    with open(gm_notes_file, "r", encoding="utf-8") as gmf:
                        gm_notes_raw = gmf.read()

            # Skip if no notes found or string is empty
            if not gm_notes_raw or str(gm_notes_raw).strip() == "":
                continue

            # Load the internal GMNotes JSON string
            try:
                gm_notes_data = json.loads(gm_notes_raw)
            except (json.JSONDecodeError, TypeError):
                # If it's not a valid JSON string, we skip it
                continue

            # Check for the "id" field in the GMNotes
            id = gm_notes_data.get("id")

            if id not in UPDATE_MAP:
                continue

            match_count += 1

            # Perform the Update
            updated_data = update_json_data(data, id)

            # Save the file back
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(updated_data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"Successfully updated: {file} (ID: {id})")

    print(f"Done! Scanned {processed_count} files, updated {match_count} files.")


if __name__ == "__main__":
    process_json_files()
