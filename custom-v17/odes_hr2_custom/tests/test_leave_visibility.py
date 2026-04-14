from odoo.tests import common


class TestLeaveVisibility(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.group_user = self.env.ref("base.group_user")
        self.group_department_manager = self.env.ref(
            "odes_hr2_custom.group_department_time_off_manager"
        )
        self.group_hr_full = self.env.ref("odes_hr2_custom.group_see_all_record_hr")
        self.leave_type = self.env["hr.leave.type"].search([], limit=1)

        self.department_manager_user = self.env["res.users"].create(
            {
                "name": "Department Manager",
                "login": "dept_manager_leave",
                "email": "dept.manager.leave@example.com",
                "groups_id": [
                    (6, 0, [self.group_user.id, self.group_department_manager.id])
                ],
            }
        )
        self.hr_full_user = self.env["res.users"].create(
            {
                "name": "HR Full",
                "login": "hr_full_leave",
                "email": "hr.full.leave@example.com",
                "groups_id": [(6, 0, [self.group_user.id, self.group_hr_full.id])],
            }
        )
        self.employee_user = self.env["res.users"].create(
            {
                "name": "Department Employee",
                "login": "dept_employee_leave",
                "email": "dept.employee.leave@example.com",
                "groups_id": [(6, 0, [self.group_user.id])],
            }
        )
        self.other_user = self.env["res.users"].create(
            {
                "name": "Other Employee",
                "login": "other_employee_leave",
                "email": "other.employee.leave@example.com",
                "groups_id": [(6, 0, [self.group_user.id])],
            }
        )

        self.department = self.env["hr.department"].create({"name": "Quality"})
        self.other_department = self.env["hr.department"].create({"name": "Sales"})

        self.manager_employee = self.env["hr.employee"].create(
            {
                "name": "Department Manager Employee",
                "user_id": self.department_manager_user.id,
                "department_id": self.department.id,
            }
        )
        self.department.manager_id = self.manager_employee

        self.employee = self.env["hr.employee"].create(
            {
                "name": "Department Employee Record",
                "user_id": self.employee_user.id,
                "department_id": self.department.id,
            }
        )
        self.other_employee = self.env["hr.employee"].create(
            {
                "name": "Other Department Employee Record",
                "user_id": self.other_user.id,
                "department_id": self.other_department.id,
            }
        )

        leave_model = self.env["hr.leave"].with_user(self.hr_full_user)
        self.department_leave = leave_model.create(
            {
                "holiday_type": "employee",
                "holiday_status_id": self.leave_type.id,
                "employee_id": self.employee.id,
            }
        )
        self.other_leave = leave_model.create(
            {
                "holiday_type": "employee",
                "holiday_status_id": self.leave_type.id,
                "employee_id": self.other_employee.id,
            }
        )

    def test_department_manager_only_sees_department_leave(self):
        visible = self.env["hr.leave"].with_user(self.department_manager_user).search([])
        self.assertIn(self.department_leave, visible)
        self.assertNotIn(self.other_leave, visible)

    def test_hr_full_group_sees_all_leaves(self):
        visible = self.env["hr.leave"].with_user(self.hr_full_user).search([])
        self.assertIn(self.department_leave, visible)
        self.assertIn(self.other_leave, visible)
