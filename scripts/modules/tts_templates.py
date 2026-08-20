SAVED_OBJECT = {
    "SaveName": "",
    "Date": "",
    "VersionNumber": "",
    "GameMode": "",
    "GameType": "",
    "GameComplexity": "",
    "Gravity": 0.5,
    "PlayArea": 0.5,
    "Table": "",
    "Sky": "",
    "Note": "",
    "TabStates": {},
    "ObjectStates": [],
}

BAG = {
    "Name": "Bag",
    "Transform": {
        "rotY": 180,
        "scaleX": 1,
        "scaleY": 1,
        "scaleZ": 1,
    },
}

CARD = {
    "Name": "Card",
    "Transform": {
        "rotY": 180,
        "scaleX": 1,
        "scaleY": 1,
        "scaleZ": 1,
    },
    "HideWhenFaceDown": True,
}

MODEL = {
    "ColorDiffuse": {
        "a": 0,
        "b": 0,
        "g": 0,
        "r": 0,
    },
    "CustomMesh": {
        "CustomShader": {
            "FresnelStrength": 0,
            "SpecularColor": {
                "b": 1,
                "g": 1,
                "r": 1,
            },
            "SpecularIntensity": 0,
            "SpecularSharpness": 2,
        },
        "DiffuseURL": "",
        "MaterialIndex": 3,
        "MeshURL": "",
        "TypeIndex": 4,
    },
    "Hands": False,
    "HideWhenFaceDown": False,
    "Locked": True,
    "Name": "Custom_Model",
    "Tooltip": False,
    "Transform": {
        "rotY": 180,
        "scaleX": 1,
        "scaleY": 1,
        "scaleZ": 1,
    },
}

TILE = {
    "ColorDiffuse": {
        "b": 1,
        "g": 1,
        "r": 1,
    },
    "CustomImage": {
        "CustomTile": {
            "Stackable": True,
            "Stretch": True,
            "Thickness": 0.1,
            "Type": 2,
        },
        "ImageScalar": 1,
        "ImageSecondaryURL": "",
        "ImageURL": "",
        "WidthScale": 0,
    },
    "Hands": False,
    "HideWhenFaceDown": False,
    "Name": "Custom_Tile",
    "Snap": False,
    "Transform": {
        "rotY": 180,
        "scaleX": 1,
        "scaleY": 1,
        "scaleZ": 1,
    },
}

TOKEN = {
    "ColorDiffuse": {
        "b": 1,
        "g": 1,
        "r": 1,
    },
    "CustomImage": {
        "CustomToken": {
            "MergeDistancePixels": 10,
            "Stackable": False,
            "StandUp": False,
            "Thickness": 0.3,
        },
        "ImageScalar": 1,
        "ImageURL": "",
        "WidthScale": 0,
    },
    "Hands": False,
    "HideWhenFaceDown": False,
    "Locked": True,
    "Name": "Custom_Token",
    "Snap": False,
    "Transform": {
        "rotY": 180,
        "scaleX": 1,
        "scaleY": 1,
        "scaleZ": 1,
    },
}

PDF = {
    "ColorDiffuse": {
        "b": 1,
        "g": 1,
        "r": 1,
    },
    "CustomPDF": {
        "PDFPage": 0,
        "PDFPageOffset": 0,
        "PDFPassword": "",
        "PDFUrl": "",
    },
    "Hands": False,
    "HideWhenFaceDown": False,
    "Name": "Custom_PDF",
    "Transform": {
        "rotY": 180,
        "scaleX": 1,
        "scaleY": 1,
        "scaleZ": 1,
    },
}
