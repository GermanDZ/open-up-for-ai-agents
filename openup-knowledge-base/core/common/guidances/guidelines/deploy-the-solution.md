---
title: Deploy the Solution
source_url: core.mgmt.common.extend_supp/guidances/guidelines/deploying_the_solution_A64311AA.html
type: Guideline
uma_name: deploying_the_solution
page_guid: _yYlQoC3xEdycYKq0PulnEQ
keywords:
- deploy
- solution
related:
  tasks:
  - assess-results-1
  - plan-iteration-1
  - plan-project-1
---


 This guideline describes activities that usually take place when moving the developed software into production.
---

Relationships

Related Elements|
  * [Assess Results](../../../../practice-management/iterative_dev/tasks/assess-results-1.md)
  * [Plan Iteration](../../../../practice-management/iterative_dev/tasks/plan-iteration-1.md)
  * [Plan Project](../../../../practice-management/release_planning/tasks/plan-project-1.md)
---|---

Main Description

###  Planning transition iterations

Software may be deployed into a production environment at the end of any Construction or Transition iteration. Deployment to production before the end of the project may be done to drive down risk by validating the application, deployment scripts, deployment environment, and to get valuable feedback from operations and systems teams, as well as end users. These early deployments are often done on a limited scale in terms of target audience or only partial applications are deployed. For the deployment to work, one or several iterations are focused on work necessary to successfully release the system. In the Transition phase, one or several iterations may be dedicated to preparing for a smooth deployment. The number of iterations depends on the complexity of the system and various other factors, as listed here. When planning for deployment, the Work Items list should be updated with relevant tasks related to these considerations:
  * Resolving defects
  * Testing installation or deployment scripts to avoid surprises in actual deployment
  * Updating any operations and support test environments used to simulate production problems
  * Performing release-specific testing efforts, such as pilot or beta testing,to a subset of your end-user community where the system is deployed
  * Conducting acceptance reviews with stakeholders, including a final release acceptance testing effort where people outside of the team are involved and decide whether it truly meets their needs
  * Finalizing relevant documentation, such as operations and system manuals, end-user documentation and release notes
  * Creating physical collateral, such as installation media
  * Replacing or installing physical assets, or both, including workstations, servers, and network components
  * Replacing existing software with new versions
  * Updating existing databases, including any relevant data migration and database schema changes
  * Production data population
  * Training end users and operations and support staff
  * Fixing any discrepancies discovered during the transition phase
  * Setting up management and operational systems and processes
  * Training the team that is taking over maintenance and evolution of the system
  * Deploying the software to the production environment

When the team and stakeholders are reviewing late Construction and early Transition iterations, the team should gather feedback from actual stakeholders' use of the product and take that information into consideration when prioritizing the work for the next iteration.  See \[[AMB07](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#AMB07)\] for more information.

###  Reviewing transition iterations

Transition iteration reviews have a different focus from other iterations in the project lifecycle. The goal is not to brainstorm about what features to develop next. Instead, reviews will assess the release management resources and procedures, the quality of the software, and how prepared users and operations teams are to face a move of the software into the production environment.
---
