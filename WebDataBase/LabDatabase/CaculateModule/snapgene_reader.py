import struct
import html2text
import xmltodict
try:
    # Biopython <1.78
    from Bio.Alphabet import DNAAlphabet

    has_dna_alphabet = True
except ImportError:
    # Biopython >=1.78
    has_dna_alphabet = False
    
HTML_PARSER = html2text.HTML2Text()
HTML_PARSER.ignore_emphasis = True
HTML_PARSER.ignore_links = True
HTML_PARSER.body_width = 0
HTML_PARSER.single_line_break = True
def parse(val):
    """Parse html."""
    if isinstance(val, str):
        return HTML_PARSER.handle(val).strip().replace("\n", " ").replace('"', "'")
    else:
        return val
    
def parse_dict(obj):
    """Parse dict in the obj."""
    if isinstance(obj, dict):
        for key in obj:
            if isinstance(obj[key], str):
                obj[key] = parse(obj[key])
            elif isinstance(obj[key], dict):
                parse_dict(obj[key])
    return obj


def snapgene_to_dict(file_obj):
    if file_obj.read(1) != b"\t":
        raise ValueError("Wrong format for a SnapGene file!")

    def unpack(size, mode):
        """Unpack the fileobject."""
        return struct.unpack(">" + mode, file_obj.read(size))[0]

    # READ THE DOCUMENT PROPERTIES
    length = unpack(4, "I")
    title = file_obj.read(8).decode("ascii")
    if length != 14 or title != "SnapGene":
        raise ValueError("Wrong format for a SnapGene file !")

    data = dict(
        isDNA=unpack(2, "H"),
        exportVersion=unpack(2, "H"),
        importVersion=unpack(2, "H"),
        features=[],
    )

    while True:
        if(file_obj.closed):
            raise ValueError("文件已关闭")
        try:
            next_byte = file_obj.read(1)
            if next_byte == b"":
                break
            block_size = unpack(4, "I")
        
            temp = ord(next_byte)
            if ord(next_byte) == 0:
                # READ THE SEQUENCE AND ITS PROPERTIES
                props = unpack(1, "b")
                data["dna"] = dict(
                    topology="circular" if props & 0x01 else "linear",
                    strandedness="double" if props & 0x02 > 0 else "single",
                    damMethylated=props & 0x04 > 0,
                    dcmMethylated=props & 0x08 > 0,
                    ecoKIMethylated=props & 0x10 > 0,
                    length=block_size - 1,
                )
                data["seq"] = file_obj.read(block_size - 1).decode("ascii")
                # break
            elif ord(next_byte) == 6:
                block_content = file_obj.read(block_size - 1).decode("utf-8")
                note_data = parse_dict(xmltodict.parse(block_content))
                data["notes"] = note_data["Notes"]
            elif ord(next_byte) == 10:
                # READ THE FEATURES
                strand_dict = {"0": ".", "1": "+", "2": "-", "3": "="}
                format_dict = {"@text": parse, "@int": int}
                try:
                    features_data = xmltodict.parse(file_obj.read(block_size))
                except Exception as e:
                    continue
                features = features_data["Features"]["Feature"]
                if not isinstance(features, list):
                    features = [features]
                for feature in features:
                    segments = feature["Segment"]
                    if not isinstance(segments, list):
                        segments = [segments]
                    segments_ranges = [
                        sorted([int(e) for e in segment["@range"].split("-")])
                        for segment in segments
                    ]
                    qualifiers = feature.get("Q", [])
                    if not isinstance(qualifiers, list):
                        qualifiers = [qualifiers]
                    parsed_qualifiers = {}
                    for qualifier in qualifiers:
                        if qualifier["V"] is None:
                            pass
                        elif isinstance(qualifier["V"], list):
                            if len(qualifier["V"][0].items()) == 1:
                                parsed_qualifiers[qualifier["@name"]] = l_v = []
                                for e_v in qualifier["V"]:
                                    fmt, value = e_v.popitem()
                                    fmt = format_dict.get(fmt, parse)
                                    l_v.append(fmt(value))
                            else:
                                parsed_qualifiers[qualifier["@name"]] = d_v = {}
                                for e_v in qualifier["V"]:
                                    (fmt1, value1), (_, value2) = e_v.items()
                                    fmt = format_dict.get(fmt1, parse)
                                    d_v[value2] = fmt(value1)
                        else:
                            fmt, value = qualifier["V"].popitem()
                            fmt = format_dict.get(fmt, parse)
                            parsed_qualifiers[qualifier["@name"]] = fmt(value)

                    if "label" not in parsed_qualifiers:
                        parsed_qualifiers["label"] = feature["@name"]
                    if "note" not in parsed_qualifiers:
                        parsed_qualifiers["note"] = []
                    if not isinstance(parsed_qualifiers["note"], list):
                        parsed_qualifiers["note"] = [parsed_qualifiers["note"]]
                    color = segments[0]["@color"]
                    parsed_qualifiers["note"].append("color: " + color)

                    data["features"].append(
                        dict(
                            start=min([start for (start, end) in segments_ranges]),
                            end=max([end for (start, end) in segments_ranges]),
                            strand=strand_dict[feature.get("@directionality", "0")],
                            type=feature["@type"],
                            name=feature["@name"],
                            color=segments[0]["@color"],
                            textColor="black",
                            segments=segments,
                            row=0,
                            isOrf=False,
                            qualifiers=parsed_qualifiers,
                        )
                    )
            else:
                # WE IGNORE THE WHOLE BLOCK
                file_obj.read(block_size)
        except Exception as e:
            break

    return data

if __name__ == "__main__":
    pass
    