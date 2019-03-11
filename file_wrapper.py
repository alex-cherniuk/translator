import csv


class FileWrapper(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.changed = False

    @property
    def text(self):
        if self.file_path != "Untitled":
            return self.read_file(self.file_path)
        return ""

    @property
    def rows(self):
        return self.text.split('\n')

    @property
    def filename(self):
        return self.file_path.split('/')[-1]

    @property
    def lexemes_path(self):
        return "".join(self.file_path.split('.')[:-1]) + "_lexemes.csv"

    @property
    def identifiers_path(self):
        return "".join(self.file_path.split('.')[:-1]) + "_identifiers.csv"

    @property
    def constants_path(self):
        return "".join(self.file_path.split('.')[:-1]) + "_constants.csv"

    @property
    def postfix_history_path(self):
        return "".join(self.file_path.split('.')[:-1]) + "_postfix_history.csv"

    @property
    def postfix_marks_path(self):
        return "".join(self.file_path.split('.')[:-1]) + "_marks.csv"

    @property
    def variables_path(self):
        return "".join(self.file_path.split('.')[:-1]) + "_variables.csv"

    @staticmethod
    def read_file(file_path):
        with open(file_path, 'r') as openfile:
            return openfile.read()

    @staticmethod
    def write_file(file_path, text):
        with open(file_path, 'w') as output_file:
            output_file.write(text)


class CSVWrapper(object):
    def __init__(self, file_path):
        self.file_path = file_path

    @property
    def text(self):
        return self.read_csv(self.file_path)

    @staticmethod
    def read_csv(file_path, delimiter=',', quotechar='"'):
        with open(file_path, 'r') as csv_file:
            row_list = list(csv.reader(csv_file, delimiter=delimiter, quotechar=quotechar))
        return CSVWrapper._get_table_view(row_list)

    @staticmethod
    def write_csv(file_path, row_list):
        with open(file_path, 'w', newline='') as output_file:
            writer = csv.writer(output_file)
            for row in row_list:
                writer.writerow(row)

    @staticmethod
    def _get_table_view(row_list):
        columns_lengths = CSVWrapper._get_columns_lengths(row_list)
        for i, word_list in enumerate(row_list):
            new_word_list = ['']*len(word_list)
            for j, word in enumerate(word_list):
                new_word_list[j] = word+" "*(columns_lengths[j]-len(word))
            row_list[i] = ' | '.join(new_word_list)
        return "\n".join(row_list)

    @staticmethod
    def _get_columns_lengths(list_2d):
        columns_lengths = [0]*len(list_2d[0])
        for list_1d in list_2d:
            for i, element in enumerate(list_1d):
                if len(element) > columns_lengths[i]:
                    columns_lengths[i] = len(element)
        return columns_lengths
