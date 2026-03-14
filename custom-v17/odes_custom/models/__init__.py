from . import ir_ui_view  # v16 validator fix: silences NameError from field-expression attrs
from . import crm_lead
from . import crm_team
from . import crm_stage
from . import ir_attachment
from . import user
from . import calendar
from . import sale
from . import currency

from . import odes_crm_stage
from . import res_partner
from . import company
from . import project

from . import mail
from . import hr

# from . import approval  # disabled: 'approvals' module not available in Community
from . import expense

from . import odes_application
from . import odes_po_type

from . import leave
# from . import mailing  # disabled: v16 mass_mailing computes statistics natively; mailing.trace no longer has 'state' field