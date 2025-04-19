from constraint import Problem

class ExamConstraints:
    def __init__(self):
        self.problem = Problem()

    def add_domain_variables(self, subjects, dates, sessions, invigilators, rooms):
        """Add variables with domains to the CSP"""
        for subject in subjects:
            subj_code = subject['code']
            self.problem.addVariable(f"date_{subj_code}", dates)
            self.problem.addVariable(f"session_{subj_code}", sessions)
            self.problem.addVariable(f"invigilator_{subj_code}", [inv['code'] for inv in invigilators])
            self.problem.addVariable(f"room_{subj_code}", rooms)

    def add_basic_constraints(self, subjects):
        """Add core constraints"""
        self._add_semester_clash_constraints(subjects)
        self._add_invigilator_availability_constraints(subjects)
        self._add_room_usage_constraints(subjects)
        self._add_department_constraints(subjects)

    def _add_semester_clash_constraints(self, subjects):
        """Prevent same-semester subjects from having exams at same date and session"""
        for i, subj1 in enumerate(subjects):
            for j, subj2 in enumerate(subjects):
                if i < j and subj1['semester'] == subj2['semester']:
                    self.problem.addConstraint(
                        lambda d1, s1, d2, s2: not (d1 == d2 and s1 == s2),
                        [f"date_{subj1['code']}", f"session_{subj1['code']}",
                         f"date_{subj2['code']}", f"session_{subj2['code']}"]
                    )

    def _add_invigilator_availability_constraints(self, subjects):
        """Ensure invigilator not assigned both FN and AN sessions same day"""
        for i, subj1 in enumerate(subjects):
            for j, subj2 in enumerate(subjects):
                if i < j:
                    self.problem.addConstraint(
                        lambda d1, inv1, s1, d2, inv2, s2: not (
                            d1 == d2 and inv1 == inv2 and 
                            ((s1 == 'FN' and s2 == 'AN') or (s1 == 'AN' and s2 == 'FN'))
                        ),
                        [f"date_{subj1['code']}", f"invigilator_{subj1['code']}", f"session_{subj1['code']}",
                         f"date_{subj2['code']}", f"invigilator_{subj2['code']}", f"session_{subj2['code']}"]
                    )
                    # Additional constraint: Invigilator can't be assigned to two exams same session same day
                    self.problem.addConstraint(
                        lambda d1, inv1, s1, d2, inv2, s2: not (
                            d1 == d2 and inv1 == inv2 and s1 == s2
                        ),
                        [f"date_{subj1['code']}", f"invigilator_{subj1['code']}", f"session_{subj1['code']}",
                         f"date_{subj2['code']}", f"invigilator_{subj2['code']}", f"session_{subj2['code']}"]
                    )

    def _add_room_usage_constraints(self, subjects):
        """Restrict only one exam per room per session"""
        for i, subj1 in enumerate(subjects):
            for j, subj2 in enumerate(subjects):
                if i < j:
                    self.problem.addConstraint(
                        lambda d1, r1, s1, d2, r2, s2: not (d1 == d2 and r1 == r2 and s1 == s2),
                        [f"date_{subj1['code']}", f"room_{subj1['code']}", f"session_{subj1['code']}",
                         f"date_{subj2['code']}", f"room_{subj2['code']}", f"session_{subj2['code']}"]
                    )

    def _add_department_constraints(self, subjects):
        """Department can have only one exam per day"""
        dept_exams = {}
        for subject in subjects:
            if subject['department'] not in dept_exams:
                dept_exams[subject['department']] = []
            dept_exams[subject['department']].append(subject)
        
        for dept, dept_subjects in dept_exams.items():
            for i, subj1 in enumerate(dept_subjects):
                for j, subj2 in enumerate(dept_subjects):
                    if i < j:
                        self.problem.addConstraint(
                            lambda d1, d2: d1 != d2,
                            [f"date_{subj1['code']}", f"date_{subj2['code']}"]
                        )

    def add_custom_constraint(self, constraint_func, variables):
        self.problem.addConstraint(constraint_func, variables)

    def get_problem(self):
        return self.problem

