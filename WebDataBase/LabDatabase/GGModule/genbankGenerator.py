fileHeader = 'LOCUS 20 bp DNA circular'
featureHeader = 'FEATURES Location/Qualifiers'
seqHeader = 'ORIGIN'
fileEnd = '//'
separator = ' ' * 4

import globalDefinition as MGB


class GenbankGenerator:
    def genGenbank(self, apePath, featureDicts):
        featureLines = list()
        wholeSeq = ''
        currentPos = 0
        for featureDict in featureDicts:
            newSeq = featureDict[MGB.seqFld]
            newPos = currentPos + len(newSeq)
            featureName = featureDict.get(MGB.nameFld, None)
            featureText = featureDict.get(MGB.textFld, None)
            if featureText:
                featureLines.append(featureText)
            elif featureName:
                featureType = featureDict.get(MGB.typeFld, MGB.deafaultFeatureType)
                directionText = featureDict.get(MGB.directionFld, MGB.defaultDirection)

                featureLine = separator + f'{featureType} {directionText} {currentPos + 1}..{newPos}'
                featureLines.append(featureLine)
                # annotationLine = f'/locus_tag="{featureName}"'
                # featureLines.append(annotationLine)
                annotationLine = separator * 2 + f'/label={featureName}'
                featureLines.append(annotationLine)

            wholeSeq = wholeSeq + newSeq
            currentPos = newPos

        lines = [fileHeader, featureHeader] + featureLines + [seqHeader, wholeSeq, fileEnd]
        apeContent = '\n'.join(lines)
        with open(apePath, 'w') as f:
            f.write(apeContent)


genbankGenerator = GenbankGenerator()

if __name__ == '__main__':
    dict_4t = {MGB.nameFld: 'scar_T', MGB.seqFld: 'tttt'}
    dict_seg = {MGB.nameFld: 'seg', MGB.seqFld: 'nnnn'}
    genbankGenerator.genGenbank('output.ape', [dict_4t, dict_seg, dict_4t])
