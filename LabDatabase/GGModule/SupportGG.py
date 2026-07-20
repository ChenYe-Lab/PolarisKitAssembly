import os
import os.path
import dnacauldron
import traceback



class SupportGG:
    def __init__(self,PartAddress_list, PartName_list):
        self.PartAddress_List = PartAddress_list
        self.PartName_List = PartName_list
        self.repository = dnacauldron.SequenceRepository()
        print(self.PartName_List)

    def assemblyPart(self,name,enzyme = "auto"):
        temp = len(self.repository.get_all_part_names())
        if(len(self.repository.get_all_part_names())!=0):
            self.repository = dnacauldron.SequenceRepository()
        print(f"part_file_address:{self.PartAddress_List}")
        print(f"part_name:{self.PartName_List}")
        try:
            self.repository.import_records(files=self.PartAddress_List,use_file_names_as_ids=True, topology='default_to_circular')
            assembly = dnacauldron.Type2sRestrictionAssembly(parts=self.PartName_List, name = name, enzyme = enzyme)
            # assembly = dnacauldron.Type2sRestrictionAssembly(parts=self.PartName_List,expect_no_unused_parts=False)
            self.simulation = assembly.simulate(sequence_repository=self.repository)
        except Exception as e:
            traceback.print_exc()
            print(e.args)
        # assert len(self.simulation.construct_records) == 1
        # assert len(self.simulation.construct_records[0]) == 8016


    def show(self, output_dir="output"):
        print("Show!!!")
        os.makedirs(output_dir, exist_ok=True)
        report_writer = dnacauldron.AssemblyReportWriter(include_mix_graphs=True, include_assembly_plots=True)
        self.simulation.write_report(output_dir, report_writer=report_writer)


    def AddPart(self, records):
        self.repository.add_records(records)

if __name__ == '__main__':
    AddressList = [r'WebDataWorld/output/50f10337-269d-4961-841b-fbc7127dcfc1/ZZ085/provided_parts_records/backbone-769-ZZ031-.gb',r'WebDataWorld/output/50f10337-269d-4961-841b-fbc7127dcfc1/ZZ085/provided_parts_records/plasmid-8244-ZZ014-phiBT1 Integrase.gb']
    FileName = ['backbone-769-ZZ031-', 'plasmid-8244-ZZ014-phiBT1 Integrase']
    test = SupportGG(AddressList,FileName)
    test.assemblyPart("webtest","BsaI")
    test.show()
