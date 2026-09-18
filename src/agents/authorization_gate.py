from typing import List, Tuple, Dict
from src.models import Document, UserContext, AuthorizationDecision


class AuthorizationGatekeeper:
    """Deterministic Pre-LLM Authorization Gatekeeper.
    
    Guarantees that unauthorized documents are dropped deterministically BEFORE
    reaching prompt construction or the LLM. Content of rejected documents is
    never exposed.
    """

    def evaluate(
        self, candidate_docs: List[Document], user: UserContext
    ) -> Tuple[List[Document], List[Document], Dict[str, AuthorizationDecision]]:
        """Evaluates each candidate document against user clearance, department, and role.
        
        Returns:
            authorized_docs: Documents permitted for this user.
            unauthorized_docs: Documents blocked from this user.
            decisions: Mapping of document_id -> AuthorizationDecision with reasons.
        """
        authorized_docs: List[Document] = []
        unauthorized_docs: List[Document] = []
        decisions: Dict[str, AuthorizationDecision] = {}

        for doc in candidate_docs:
            reasons: List[str] = []

            # 1. Clearance Check (Hierarchy: Public=0 < Internal=1 < Confidential=2 < Restricted=3)
            if user.clearance < doc.classification:
                reasons.append(
                    f"Clearance insufficient: User has {user.clearance.name.capitalize()}, "
                    f"document requires {doc.classification.name.capitalize()}"
                )

            # 2. Department Check
            if doc.allowed_departments and "*" not in doc.allowed_departments:
                dept_match = any(
                    dept.strip().lower() == user.department.strip().lower()
                    for dept in doc.allowed_departments
                )
                if not dept_match:
                    reasons.append(
                        f"Department mismatch: User is in '{user.department}', "
                        f"allowed departments: {doc.allowed_departments}"
                    )

            # 3. Role Check
            if doc.allowed_roles and "*" not in doc.allowed_roles:
                role_match = any(
                    role.strip().lower() == user.role.strip().lower()
                    for role in doc.allowed_roles
                )
                if not role_match:
                    reasons.append(
                        f"Role mismatch: User has role '{user.role}', "
                        f"allowed roles: {doc.allowed_roles}"
                    )

            is_authorized = len(reasons) == 0
            decision = AuthorizationDecision(
                document_id=doc.document_id,
                authorized=is_authorized,
                reasons=reasons,
                classification=doc.classification.name.capitalize(),
                allowed_departments=doc.allowed_departments,
                allowed_roles=doc.allowed_roles,
            )
            decisions[doc.document_id] = decision

            if is_authorized:
                authorized_docs.append(doc)
            else:
                unauthorized_docs.append(doc)

        return authorized_docs, unauthorized_docs, decisions
