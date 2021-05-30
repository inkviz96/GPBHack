from django.shortcuts import render
from django.views import View
from scp import SCPClient
from .mixins import RequestDataMixin
from .utils import Parser
from django.db import connections
import requests
import paramiko
from .models import *
from django.db.models import Q


class DetailDecisionsView(RequestDataMixin, View):
    """ Get -запрос, который позволяет по sourceURI определить подробные параметры решения.
    """
    def __init__(self):
        super(DetailDecisionsView, self).__init__()
        self.sourceURI = '9c529dea-6b72-4fee-bffb-368a75bc07a3/revisions/164159ad-b9df-423b-b304-389c5bbe3859'
        self.signatures_list = []
        self.signatures_dict = {}

    def get(self, request, *args, **kwargs):
        self.get_token()
        response_SAS = requests.get(self.host + 'decisions/flows/' + self.sourceURI, headers=self.headers)
        content = response_SAS.json()
        context = {'title': "Подробные параметры решения", 'content': content['signature']}
        return render(request, 'sas_rtdm/sas_id_data.html', context)


class DecisionsView(RequestDataMixin, View):
    """ Get -запрос, который позволяет по sourceURI определить подробные параметры решения.
    """
    def __init__(self):
        super(DecisionsView, self).__init__()
        self.sourceURI = ''
        self.signatures_list = []
        self.signatures_dict = {}

    def get(self, request, *args, **kwargs):
        self.get_token()
        response_SAS = requests.get(self.host + 'decisions/flows/' + self.sourceURI, headers=self.headers)
        content = response_SAS.json()
        context = {'title': "Параметры решения", 'content': content['items']}
        return render(request, 'sas_rtdm/sas_id_data.html', context)


class CheckRulesSetView(RequestDataMixin, View):
    """ Get -запрос, который позволяет определить все существующие на сервере rule sets.
    """
    def __init__(self):
        super(CheckRulesSetView, self).__init__()

    def get(self, request, *args, **kwargs):
        response_SAS = requests.get(self.host + '/businessRules/ruleSets', headers=self.headers)
        content = response_SAS.json()
        context = {'title': "Наборы правил", 'content': content['items']}
        return render(request, 'sas_rtdm/sas_id_data.html', context)


class CheckLookups(RequestDataMixin, View):
    """ Get -запрос, который позволяет определить все существующие на сервере rule sets.
    """
    def __init__(self):
        super(CheckLookups, self).__init__()

    def get(self, request, *args, **kwargs):
        response_SAS = requests.get(
            self.host + '/referenceData/domains',headers=self.headers)
        content = response_SAS.json()
        context = {'title': "Наборы правил", 'content': content['items']}
        return render(request, 'sas_rtdm/sas_id_data.html', context)


class GetRTDMData(View):
    def __init__(self):
        super(GetRTDMData, self).__init__()
        self.host = '217.73.57.195'
        self.url = 'http://' + self.host + ':7980/SASCIStudio'
        self.user = 'sas'
        self.password = '#Orion123_'
        self.port = 22
        self.xml_files = [
            'request_main.xml', 'request_result.xml', 'request_client.xml', 'request_doc.xml', 'request_address.xml']

    def my_custom_sql(request):
        table_names = []
        table_results = []
        subject = ''
        with connections['ms'].cursor() as cursor:
            if subject == '':
                items = cursor.execute('''SELECT TABLE_NAME
                                        FROM INFORMATION_SCHEMA.TABLES
                                        WHERE table_type='BASE TABLE' AND TABLE_NAME != 'sysdiagrams'
                                        ''')
                for item in items:
                    table_names.append(item)
            else:
                for item in subject:
                    table_names.append(item)
            for table_name in table_names:
                items = (cursor.execute('''SELECT
                                TABLE_NAME,
                                COLUMN_NAME,
                                DATA_TYPE,
                                IS_NULLABLE
                                FROM INFORMATION_SCHEMA.COLUMNS
                                WHERE table_name={}
                                '''.format('\'' + str(table_name[0]) + '\'')))
                for item in items:
                    table_results.append(item)
        return table_results

    def checkRTDMdata(self, request):
        res = self.my_custom_sql()
        SAS = CheckSAS.objects.last()
        diagram = Diagram.objects.all().filter(diagram_list=SAS)
        processes = Processes.objects.all().filter(diagram__in=diagram)
        input = Input.objects.all().filter(processes__in=processes)
        output = Output.objects.all().filter(processes__in=processes)
        l = []
        yes = []
        for x in input:
            if x.type == 'data grid':
                gh = 'data'
            elif x.type == 'date list':
                gh = 'data'
            elif x.type == 'double list':
                gh = 'double'
            elif x.type == 'string list':
                gh = 'string'
            else:
                gh = x.type
            l.append([x.processes.table_name, x.name, gh])
        for i in res:
            if i[2] == 'numeric':
                i[2] = 'double'
            if i[2] == 'nvarchar' or i[2] == 'varchar' or i[2] == 'string list':
                i[2] = 'string'

            r = [i[0], i[1], i[2]]
            yes.append(r)
        k = []
        for i in l:
            if i not in yes:
                k.append(i)
            else:
                pass

        b = []
        p = []

        for x in output:
            if x.type == 'data grid':
                gh = 'data'
            elif x.type == 'date list':
                gh = 'data'
            elif x.type == 'double list':
                gh = 'double'
            elif x.type == 'string list':
                gh = 'string'
            else:
                gh = x.type
            b.append([x.processes.table_name, x.name, gh])
        for i in b:
            if i not in yes:
                p.append(i)
            else:
                pass
        return [k, p]

    def temp(self):
        SAS = CheckSAS.objects.last()
        diagram = Diagram.objects.all().filter(diagram_list=SAS)
        processes = Processes.objects.all().filter(diagram__in=diagram)
        input = Input.objects.all().filter(processes__in=processes)
        output = Output.objects.all().filter(processes__in=processes)
        subdiagram = SubDiagram.objects.all().filter(diagram__in=diagram)
        context = {'diagrams': diagram, 'inputs': input, 'outputs': output, 'subdiagrams': subdiagram, 'processes': processes}
        return context

    def get(self, request, *args, **kwargs):
        dead_process = []
        new_check = CheckSAS.objects.create()
        for file in self.xml_files:
            self.download_xml(file=file)
            parser = Parser('out.xml')
            parser.parse_xml(new_check)

        last_check_data = self.temp()
        for process in last_check_data['processes']:
            if process.source == 'Cell':
                dead_process.append(process)
        context = self.temp()
        r = self.checkRTDMdata(request)
        #inp = []
        #out = []
        #for x in r[0]:
        #    processes = Processes.objects.all().filter(table_name=x[0])
        #    a = Input.objects.filter(processes__in=processes, name=x[1], type=x[2])
        #    for x in a:
        #        inp.append([x.name, x.type, x.processes])
        #for x in r[1]:
        #    processes = Processes.objects.all().filter(table_name=x[0])
        #    a = Output.objects.filter(Q(processes__in=processes)| Q(name=x[1])| Q(type=x[2]))
        #    for x in a:
        #        out.append([x.name, x.type, x.processes])
        context['dead'] = dead_process
        context['input'] = r[0]
        context['output'] = r[1]
        return render(request, 'sas_rtdm/list.html', context=context)

    def download_xml(self, file):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.host,
            username=self.user,
            password=self.password,
            port=self.port,
            banner_timeout=400,
            auth_timeout=200)
        stdin, stdout, stderr = client.exec_command('sudo -S rm *')
        stdin.write(self.password + '\n')
        stdin.flush()

        stdin, stdout, stderr = client.exec_command(
            f'/opt/sas/sashome/SASMarketingAutomationIntegrationUtilities/6.6/sasmaextract cisample@saspw Orion123 DefaultAuth "HACK" "/opt/sas/sashome/SASMarketingAutomationIntegrationUtilities/6.6/{file}" "/opt/sas/sashome/SASMarketingAutomationIntegrationUtilities/6.6/out.xml"')
        data = stdout.read() + stderr.read()
        scp = SCPClient(client.get_transport())
        scp.get('/opt/sas/sashome/SASMarketingAutomationIntegrationUtilities/6.6/out.xml')
        client.close()
        scp.close()

        return data.decode('UTF-8')
