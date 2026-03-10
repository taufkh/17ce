from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ApprovalCategory(models.Model):
    _name = 'approval.category'
    _description = 'Approval Category'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    automated_sequence = fields.Boolean()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    image = fields.Binary()
    has_amount = fields.Selection(
        [('no', 'No'), ('optional', 'Optional'), ('required', 'Required')],
        default='no',
        required=True,
    )
    requirer_document = fields.Selection(
        [('no', 'No'), ('required', 'Required')],
        default='no',
        required=True,
    )
    approval_minimum = fields.Integer(default=1)
    approver_ids = fields.One2many('approval.category.approver', 'category_id', string='Default Approvers')
    request_to_validate_count = fields.Integer(compute='_compute_request_to_validate_count')

    def _compute_request_to_validate_count(self):
        for category in self:
            category.request_to_validate_count = self.env['approval.request'].search_count([
                ('category_id', '=', category.id),
                ('request_status', '=', 'pending'),
                ('approver_ids.user_id', '=', self.env.user.id),
                ('approver_ids.status', '=', 'pending'),
            ])

    def create_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Approval Request'),
            'res_model': 'approval.request',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_category_id': self.id,
                'default_request_owner_id': self.env.user.id,
            },
        }


class ApprovalCategoryApprover(models.Model):
    _name = 'approval.category.approver'
    _description = 'Approval Category Approver'
    _order = 'sequence,id'

    sequence = fields.Integer(default=10)
    category_id = fields.Many2one('approval.category', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True)


class ApprovalRequest(models.Model):
    _name = 'approval.request'
    _description = 'Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    category_id = fields.Many2one('approval.category', required=True, tracking=True)
    request_owner_id = fields.Many2one('res.users', default=lambda self: self.env.user, tracking=True)
    date = fields.Date(default=fields.Date.context_today)
    date_confirmed = fields.Datetime()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    amount = fields.Monetary(currency_field='currency_id', tracking=True)
    has_amount = fields.Selection(related='category_id.has_amount', store=False)
    requirer_document = fields.Selection(related='category_id.requirer_document', store=False)
    attachment_number = fields.Integer(compute='_compute_attachment_number')
    request_status = fields.Selection(
        [
            ('new', 'New'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
            ('cancel', 'Cancelled'),
        ],
        default='new',
        compute='_compute_request_status',
        store=True,
        tracking=True,
    )
    approver_ids = fields.One2many('approval.approver', 'request_id', string='Approvers')
    reason = fields.Text(string='Reason')

    def _is_manager(self):
        return self.env.user.has_group('approvals.group_approval_manager')

    @api.depends('message_attachment_count')
    def _compute_attachment_number(self):
        for request in self:
            request.attachment_number = request.message_attachment_count

    @api.depends('approver_ids.status')
    def _compute_request_status(self):
        for request in self:
            statuses = request.approver_ids.mapped('status')
            if not statuses:
                request.request_status = 'new'
                continue
            if 'refused' in statuses:
                request.request_status = 'refused'
                continue
            approved_count = len(request.approver_ids.filtered(lambda line: line.status == 'approved'))
            min_required = max(1, request.category_id.approval_minimum or 1)
            if approved_count >= min_required:
                request.request_status = 'approved'
            elif 'pending' in statuses:
                request.request_status = 'pending'
            elif 'new' in statuses:
                request.request_status = 'new'
            elif 'cancel' in statuses:
                request.request_status = 'cancel'
            else:
                request.request_status = 'pending'

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if not self.category_id:
            return
        self.approver_ids = [(5, 0, 0)]
        for line in self.category_id.approver_ids:
            self.approver_ids += self.env['approval.approver'].new({
                'user_id': line.user_id.id,
                'status': 'new',
            })

    def _get_user_approval_activities(self, user):
        return self.env['mail.activity'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
            ('user_id', '=', user.id),
        ])

    def action_confirm(self):
        for request in self:
            if request.request_owner_id != self.env.user and not request._is_manager():
                raise UserError(_('Only the requester or approval manager can submit this request.'))
            if request.requirer_document == 'required' and not request.attachment_number:
                raise UserError(_('You have to attach at least one document.'))
            if not request.approver_ids:
                raise UserError(_('You have to add at least one approver.'))

            request.approver_ids.write({'status': 'pending'})
            request.approver_ids._create_activity()
            request.date_confirmed = fields.Datetime.now()
        return True

    def action_approve(self, approver=None):
        for request in self:
            if not isinstance(approver, models.BaseModel):
                approver = request.approver_ids.filtered(lambda a: a.user_id == self.env.user and a.status == 'pending')[:1]
            if not approver:
                raise UserError(_('No pending approval line for current user.'))

            approver.write({'status': 'approved'})
            request._get_user_approval_activities(self.env.user).action_feedback()
            min_required = max(1, request.category_id.approval_minimum or 1)
            approved_count = len(request.approver_ids.filtered(lambda line: line.status == 'approved'))
            if approved_count >= min_required:
                request.approver_ids.filtered(lambda line: line.status in ('new', 'pending')).write({'status': 'cancel'})
        return True

    def action_refuse(self):
        for request in self:
            approver = request.approver_ids.filtered(lambda a: a.user_id == self.env.user and a.status == 'pending')[:1]
            if not approver:
                raise UserError(_('No pending approval line for current user.'))
            approver.write({'status': 'refused'})
            request._get_user_approval_activities(self.env.user).action_feedback()
        return True

    def action_cancel(self):
        for request in self:
            if request.request_owner_id != self.env.user and not request._is_manager():
                raise UserError(_('Only the requester or approval manager can cancel this request.'))
            for line in request.approver_ids.filtered(lambda l: l.status in ('new', 'pending')):
                line.status = 'cancel'
            request._get_user_approval_activities(self.env.user).action_feedback()
        return True

    def action_draft(self):
        for request in self:
            if request.request_owner_id != self.env.user and not request._is_manager():
                raise UserError(_('Only the requester or approval manager can reset this request.'))
            request.approver_ids.write({'status': 'new'})
        return True


class ApprovalApprover(models.Model):
    _name = 'approval.approver'
    _description = 'Approval Approver'
    _order = 'sequence,id'

    sequence = fields.Integer(default=10)
    request_id = fields.Many2one('approval.request', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True)
    status = fields.Selection(
        [
            ('new', 'New'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
            ('cancel', 'Cancelled'),
        ],
        default='new',
        required=True,
    )

    def _create_activity(self):
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        for approver in self:
            existing = self.env['mail.activity'].sudo().search([
                ('res_model', '=', 'approval.request'),
                ('res_id', '=', approver.request_id.id),
                ('user_id', '=', approver.user_id.id),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if not existing:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env['ir.model']._get_id('approval.request'),
                    'res_id': approver.request_id.id,
                    'activity_type_id': activity_type.id,
                    'user_id': approver.user_id.id,
                    'summary': _('Approval Needed'),
                    'note': _('Please review and process this approval request.'),
                })
