# import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_round
from xlsxwriter.utility import xl_rowcol_to_cell


import logging
_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.debug('Cannot `import xlsxwriter`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')

class MandaysMonthlyReportWizard(models.TransientModel):
    _name = 'mandays.monthly.report.wizard'
    _description = 'Mandays Monthly Report Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    document = fields.Binary('File To Download')
    is_done = fields.Boolean('Show Only Completed Tasks')
    project_ids = fields.Many2many(comodel_name='project.project', string='Project Ids')

    file = fields.Char('Report File Name', readonly=1)

    def mandays_monthly_report_xlsx(self):
        self.ensure_one()
        [data] = self.read()

        if data.get('start_date') == data.get('end_date'):
            title_date = str(data.get('start_date'))
        elif data.get('start_date').strftime("%m %Y") == data.get('end_date').strftime("%m %Y"):
            title_date = str(data.get('start_date').strftime("%d")) + " - " + str(data.get('end_date').strftime("%d")) + " " + str(data.get('start_date').strftime("%B %Y")) 
        elif data.get('start_date').strftime("%Y") == data.get('end_date').strftime("%Y"):
            title_date = str(data.get('start_date').strftime("%d %B")) + " - " + str(data.get('end_date').strftime("%d %B")) + " " + str(data.get('start_date').strftime("%Y")) 
        else:
            title_date = str(data.get('start_date').strftime("%d %B %Y")) + " - " + str(data.get('end_date').strftime("%d %B %Y")) 

        file_path = 'Mandays Monthly Report '  + title_date + '.xlsx'
        workbook = xlsxwriter.Workbook('/tmp/' + file_path)

        # title_format = workbook.add_format({'bold': True,'valign':'vcenter','font_size':10,})
        # title_center_format = workbook.add_format({'valign':'vcenter','align': 'center','font_size':10,})
        # header_table_format = workbook.add_format({'bold': True,'valign': 'top','align': 'center', 'font_size':10, 'color': '#0025f6'})
        # cell_wrap_format = workbook.add_format({'valign':'vjustify','valign':'vcenter','align': 'left','font_size':10,})
        # cell_wrap_format_right = workbook.add_format({'valign':'vjustify','valign':'vcenter','align': 'right','font_size':10,})
        # cell_wrap_format_center = workbook.add_format({'valign':'vjustify','valign':'top','align': 'center','font_size':10,})
        # currency_format = workbook.add_format({'num_format': '#,##0.00', 'valign':'vjustify','valign':'vcenter','align': 'right','font_size':10,})

        # header_table_format.set_text_wrap()

        title_format = workbook.add_format({'valign': 'vcenter', 'font_size': 12})
        info_header_format = workbook.add_format({'bold': True,'valign':'vcenter','font_size':12})
        table_header_format = workbook.add_format({'bold': True,'valign':'vcenter', 'align': 'center', 'font_size':12})
        
        # self._cr.execute('''
        #         SELECT dev.name as title, dev.mandays as mandays, dev.user as assigned,dev.start_date as start_date, dev.end_date as end_date, dev.stage as stage, req.module_id as apps, req.number as number, req.name as req_title
        #         FROM odes_crm_requirement_task as dev
        #         LEFT JOIN odes_crm_requirement as req
        #         on dev.requirement_id = req.id
        #         WHERE dev.start_date::date BETWEEN %s AND %s
        #     ''',(self.start_date, self.end_date))
        # dev_task_data = self.env.cr.dictfetchall()

        # print(dev_task_data, 'see here dev task dataa \n\n\n\n\n')
        dev_task_obj = self.env['odes.crm.requirement.task'].sudo()
        requirement_obj = self.env['odes.crm.requirement'].sudo()
        draft_requirement_obj = self.env['odes.crm.requirement.draft'].sudo()
        project_obj = self.env['project.project'].sudo()

        project_ids = []
        dev_task = dev_task_obj.search([('start_date', '>=', self.start_date), ('end_date', '<=', self.end_date)])
        # project_dev_task = dev_task_obj.search([('requirement_id', '=', 37), ('start_date', '>=', self.start_date), ('end_date', '<=', self.end_date)])
        for task in dev_task:
            if not self.project_ids: 
                requirement = requirement_obj.search([('id', '=', task.requirement_id.id)])
                draft_requirement = draft_requirement_obj.search([('id', '=', task.draft_requirement_id.id)])
            else:
                requirement = requirement_obj.search([('id', '=', task.requirement_id.id), ('project_id', 'in', self.project_ids.ids)])
            for req in requirement:
                project = project_obj.search([('id', '=', req.project_id.id), '|', ('active', '=', False), ('active', '=', True)])
                project_ids.append(project)
            for req in draft_requirement:
                project = project_obj.search([('id', '=', req.project_id.id), '|', ('active', '=', False), ('active', '=', True)])
                project_ids.append(project)
        # print(project_ids, 'see here project ids \n\n\n\n')
        duplicate_removed_project_ids = list(dict.fromkeys(project_ids))
        # print(list(dict.fromkeys(project_ids)), 'see here project ids \n\n\n\n')

        worksheet = workbook.add_worksheet('')
        worksheet.set_row(2, 30)
        worksheet.set_row(3, 30)
        worksheet.set_column(0, 0, 25) # REQ
        worksheet.set_column(1, 1, 35) # Task Title
        worksheet.set_column(2, 2, 12) # Apps
        worksheet.set_column(3, 3, 12) # Mandays
        worksheet.set_column(4, 4, 12) # Assigned
        worksheet.set_column(5, 5, 15) # Start Date
        worksheet.set_column(6, 6, 15) # End Date
        worksheet.set_column(7, 7, 12) # Stage
        # worksheet.set_column(8, 8, 20)
        # worksheet.set_column(10, 10, 10)

        worksheet.write(0, 0, "Mandays Report", title_format)
        worksheet.write(0, 2, "Period :", title_format)
        worksheet.write(0, 3, str(self.start_date.strftime('%Y-%m-%d')), title_format)
        worksheet.write(0, 4, "to", title_format)
        worksheet.write(0, 5, str(self.end_date.strftime('%Y-%m-%d')), title_format)
        rowscol = 1
        
        # # Project Data
        # worksheet.write(2, 0,'Project :', info_header_format)
        # worksheet.write(2, 3,'Project Manager :', info_header_format)

        # # Task Data
        # worksheet.write(3, 0,'REQ', table_header_format)
        # worksheet.write(3, 1,'Task Title', table_header_format)
        # worksheet.write(3, 2,'Apps', table_header_format)
        # worksheet.write(3, 3,'Mandays', table_header_format)
        # worksheet.write(3, 4,'Assigned', table_header_format)
        # worksheet.write(3, 5,'Start Date', table_header_format)
        # worksheet.write(3, 6,'End Date', table_header_format)
        # worksheet.write(3, 7,'Stage', table_header_format)
        
        rows = 2
        grand_total_mandays = 0.0
        total_mandays = 0.0

        for header in range(0, len(duplicate_removed_project_ids)):
            worksheet.write(rows, 0, 'Project :', info_header_format)
            worksheet.write(rows, 1, duplicate_removed_project_ids[header].name, info_header_format)
            worksheet.write(rows, 3, 'Project Manager :', info_header_format)
            worksheet.write(rows, 4, duplicate_removed_project_ids[header].user_id.name, info_header_format)
            worksheet.write(rows + 1, 0,'REQ', table_header_format)
            worksheet.write(rows + 1, 1,'Task Title', table_header_format)
            worksheet.write(rows + 1, 2,'Apps', table_header_format)
            worksheet.write(rows + 1, 3,'Mandays', table_header_format)
            worksheet.write(rows + 1, 4,'Assigned', table_header_format)
            worksheet.write(rows + 1, 5,'Start Date', table_header_format)
            worksheet.write(rows + 1, 6,'End Date', table_header_format)
            worksheet.write(rows + 1, 7,'Stage', table_header_format)
            # project_dev_task = dev_task_obj.search([('requirement_id', '=', duplicate_removed_project_ids[header]), ('start_date', '>=', self.start_date), ('end_date', '<=', self.end_date)])
            # , '|', ('active', '=', False), ('active', '=', True)
            requirement = requirement_obj.search([('project_id', '=', duplicate_removed_project_ids[header].id), '|', ('active', '=', False), ('active', '=', True)])
            for req in requirement:
                if self.is_done:
                    project_dev_task = dev_task_obj.search([('requirement_id', '=', req.id), ('stage', '=', 'Done'), ('end_date', '>=', self.start_date), ('end_date', '<=', self.end_date)])
                else:
                    project_dev_task = dev_task_obj.search([('requirement_id', '=', req.id), ('end_date', '>=', self.start_date), ('end_date', '<=', self.end_date)])
                inserted_task_in_report = {}
                for task in project_dev_task:
                    if inserted_task_in_report.get(task.name, False):
                        if inserted_task_in_report[task.name]['project'] == task.project and inserted_task_in_report[task.name]['user'] == task.user and inserted_task_in_report[task.name]['start_date'] == task.start_date and inserted_task_in_report[task.name]['end_date']:
                            continue

                    total_mandays += task.mandays
                    grand_total_mandays += task.mandays
                    worksheet.write(rows + 2, 0, str(task.requirement_id.number) + ' - ' + str(req.name) )
                    worksheet.write(rows + 2, 1, task.name)
                    worksheet.write(rows + 2, 2, req.module_id.name)
                    worksheet.write(rows + 2, 3, task.mandays)
                    worksheet.write(rows + 2, 4, task.user)
                    worksheet.write(rows + 2, 5, task.start_date.strftime('%d-%b-%y'))
                    worksheet.write(rows + 2, 6, task.end_date.strftime('%d-%b-%y'))
                    worksheet.write(rows + 2, 7, task.stage)
                    rows += 1

                    inserted_task_in_report[task.name] = {
                        'project': task.project,
                        'user': task.user,
                        'start_date': task.start_date,
                        'end_date': task.end_date
                    }

            draft_requirement = draft_requirement_obj.search([('project_id', '=', duplicate_removed_project_ids[header].id), ('requirement_id', '=', False)])
            for req in draft_requirement:
                if self.is_done:
                    project_dev_task_draft = dev_task_obj.search([('draft_requirement_id', '=', req.id), ('stage', '=', 'Done'), ('end_date', '>=', self.start_date), ('end_date', '<=', self.end_date)])
                    print(project_dev_task_draft, 'see here draft requriement \n\n\n\n\n')
                else:
                    project_dev_task_draft = dev_task_obj.search([('draft_requirement_id', '=', req.id), ('end_date', '>=', self.start_date), ('end_date', '<=', self.end_date)])
                for task in project_dev_task_draft:
                    total_mandays += task.mandays
                    grand_total_mandays += task.mandays
                    worksheet.write(rows + 2, 0, "(Draft) " + str(task.draft_requirement_id.number) + ' - ' + str(req.name) )
                    worksheet.write(rows + 2, 1, task.name)
                    worksheet.write(rows + 2, 2, req.module_id.name)
                    worksheet.write(rows + 2, 3, task.mandays)
                    worksheet.write(rows + 2, 4, task.user)
                    worksheet.write(rows + 2, 5, task.start_date.strftime('%d-%b-%y'))
                    worksheet.write(rows + 2, 6, task.end_date.strftime('%d-%b-%y'))
                    worksheet.write(rows + 2, 7, task.stage)
                    rows += 1

            worksheet.write(rows + 3, 2, 'Total')
            worksheet.write(rows + 3, 3, total_mandays)
            worksheet.write(rows + 3, 4, 'Mandays')
            total_mandays = 0.0
            rows += 5

        worksheet.write(rows, 2,'Printed At', info_header_format)
        worksheet.write(rows, 3, datetime.today().strftime('%m/%d/%Y %H:%M'), info_header_format)
        worksheet.write(rows + 1, 2,'Grand Total', info_header_format)
        worksheet.write(rows + 1, 3, grand_total_mandays, info_header_format)
        worksheet.write(rows + 1, 4, 'Mandays', info_header_format)
        
        # for header in project_ids:
        #     worksheet.write(3, 0,'REQ', table_header_format)
        #     worksheet.write(3, 1,'Task Title', table_header_format)
        #     worksheet.write(3, 2,'Apps', table_header_format)
        #     worksheet.write(3, 3,'Mandays', table_header_format)
        #     worksheet.write(3, 4,'Assigned', table_header_format)
        #     worksheet.write(3, 5,'Start Date', table_header_format)
        #     worksheet.write(3, 6,'End Date', table_header_format)
        #     worksheet.write(3, 7,'Stage', table_header_format)
        # header_rows += 1
        
        # for task in dev_task:
        #     requirement = requirement_obj.search([('id', '=', task.requirement_id.id)])
        #     worksheet.write(rows, 0, str(task.requirement_id.number) + ' - ' + str(requirement.name) )
        #     worksheet.write(rows, 1, task.name)
        #     worksheet.write(rows, 2, requirement.module_id.name)
        #     worksheet.write(rows, 3, task.mandays)
        #     worksheet.write(rows, 4, task.user)
        #     worksheet.write(rows, 5, task.start_date.strftime('%d-%b-%y'))
        #     worksheet.write(rows, 6, task.end_date.strftime('%d-%b-%y'))
        #     worksheet.write(rows, 7, task.stage)
        #     rows += 1
        
        # for task in dev_task_data:
        #     worksheet.write(rows, 0, str(task['number']) + ' - ' + str(task['req_title']) )
        #     worksheet.write(rows, 1, task['title'])
        #     worksheet.write(rows, 2, task['apps'])
        #     worksheet.write(rows, 3, task['mandays'])
        #     worksheet.write(rows, 4, task['assigned'])
        #     worksheet.write(rows, 5, task['start_date'].strftime('%d-%b-%y'))
        #     worksheet.write(rows, 6, task['end_date'].strftime('%d-%b-%y'))
        #     worksheet.write(rows, 7, task['stage'])
        #     rows += 1
        

        workbook.close()
        buf = base64.b64encode(open('/tmp/' + file_path, 'rb+').read())
        self.document = buf
        self.file = 'Mandays Monthly Report'+'.xlsx'
        return {
            'res_id': self.id,
            'name': 'Files to Download',
            'view_type': 'form',
            "view_mode": 'form,tree',
            'res_model': 'mandays.monthly.report.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
