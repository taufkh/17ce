# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import base64
import datetime
import dateutil
import email
import email.policy
import hashlib
import hmac
import lxml
import logging
import pytz
import re
import socket
import time
import threading

from collections import namedtuple
from email.message import EmailMessage
from lxml import etree
from werkzeug import urls
from xmlrpc import client as xmlrpclib

from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID
from odoo.exceptions import MissingError
from odoo.osv import expression

from odoo.tools import ustr
from odoo.tools.misc import clean_context, split_every

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
		''' mail_thread model is meant to be inherited by any model that needs to
				act as a discussion topic on which messages can be attached. Public
				methods are prefixed with ``message_`` in order to avoid name
				collisions with methods of the models that will inherit from this class.

				``mail.thread`` defines fields used to handle and display the
				communication history. ``mail.thread`` also manages followers of
				inheriting classes. All features and expected behavior are managed
				by mail.thread. Widgets has been designed for the 7.0 and following
				versions of Odoo.

				Inheriting classes are not required to implement any method, as the
				default implementation will work for any model. However it is common
				to override at least the ``message_new`` and ``message_update``
				methods (calling ``super``) to add model-specific behavior at
				creation and update of a thread when processing incoming emails.

				Options:
						- _mail_flat_thread: if set to True, all messages without parent_id
								are automatically attached to the first message posted on the
								ressource. If set to False, the display of Chatter is done using
								threads, and no parent_id is automatically set.

		MailThread features can be somewhat controlled through context keys :

		 - ``mail_create_nosubscribe``: at create or message_post, do not subscribe
			 uid to the record thread
		 - ``mail_create_nolog``: at create, do not log the automatic '<Document>
			 created' message
		 - ``mail_notrack``: at create and write, do not perform the value tracking
			 creating messages
		 - ``tracking_disable``: at create and write, perform no MailThread features
			 (auto subscription, tracking, post, ...)
		 - ``mail_notify_force_send``: if less than 50 email notifications to send,
			 send them directly instead of using the queue; True by default
		'''
		_inherit = 'mail.thread'
		_description = 'Email Thread'


		def _notify_compute_recipients(self, message, msg_vals):
				""" Compute recipients to notify based on subtype and followers. This
				method returns data structured as expected for ``_notify_recipients``. """
				msg_sudo = message.sudo()
				# get values from msg_vals or from message if msg_vals doen't exists
				pids = msg_vals.get('partner_ids', []) if msg_vals else msg_sudo.partner_ids.ids
				cids = msg_vals.get('channel_ids', []) if msg_vals else msg_sudo.channel_ids.ids
				message_type = msg_vals.get('message_type') if msg_vals else msg_sudo.message_type
				subtype_id = msg_vals.get('subtype_id') if msg_vals else msg_sudo.subtype_id.id
				# is it possible to have record but no subtype_id ?
				recipient_data = {
						'partners': [],
						'channels': [],
				}
				res = self.env['mail.followers']._get_recipient_data(self, message_type, subtype_id, pids, cids)
				if not res:
						return recipient_data

				# print ('recipient_data',pids)
				author_id = msg_vals.get('author_id') or message.author_id.id
				for pid, cid, active, pshare, ctype, notif, groups in res:
						if pid and pid == author_id and not self.env.context.get('mail_notify_author'):  # do not notify the author of its own messages
								continue
						if pid:
								if self._context.get('icon_skip_partner'): #skip send email to customer when conform INV
										if pid not in pids:
												continue

								if active is False:
										continue
								pdata = {'id': pid, 'active': active, 'share': pshare, 'groups': groups or []}
								
								if notif == 'inbox':
										recipient_data['partners'].append(dict(pdata, notif=notif, type='user'))
								elif not pshare and notif:  # has an user and is not shared, is therefore user
										recipient_data['partners'].append(dict(pdata, notif=notif, type='user'))
								elif pshare and notif:  # has an user but is shared, is therefore portal
										recipient_data['partners'].append(dict(pdata, notif=notif, type='portal'))
								else:  # has no user, is therefore customer
										recipient_data['partners'].append(dict(pdata, notif=notif if notif else 'email', type='customer'))
						elif cid:
								recipient_data['channels'].append({'id': cid, 'notif': notif, 'type': ctype})

				# add partner ids in email channels
				email_cids = [r['id'] for r in recipient_data['channels'] if r['notif'] == 'email']
				if email_cids:
						# we are doing a similar search in ocn_client
						# Could be interesting to make everything in a single query.
						# ocn_client: (searching all partners linked to channels of type chat).
						# here      : (searching all partners linked to channels with notif email if email is not the author one)
						# TDE FIXME: use email_sanitized
						email_from = msg_vals.get('email_from') or message.email_from
						email_from = self.env['res.partner']._parse_partner_name(email_from)[1]
						exept_partner = [r['id'] for r in recipient_data['partners']]
						if author_id:
								exept_partner.append(author_id)
						sql_query = """ select distinct on (p.id) p.id from res_partner p
														left join mail_channel_partner mcp on p.id = mcp.partner_id
														left join mail_channel c on c.id = mcp.channel_id
														left join res_users u on p.id = u.partner_id
																where (u.notification_type != 'inbox' or u.id is null)
																and (p.email != ANY(%s) or p.email is null)
																and c.id = ANY(%s)
																and p.id != ANY(%s)"""

						self.env.cr.execute(sql_query, (([email_from], ), (email_cids, ), (exept_partner, )))
						for partner_id in self._cr.fetchall():
								# ocn_client: will add partners to recipient recipient_data. more ocn notifications. We neeed to filter them maybe
								recipient_data['partners'].append({'id': partner_id[0], 'share': True, 'active': True, 'notif': 'email', 'type': 'channel_email', 'groups': []})
				return recipient_data