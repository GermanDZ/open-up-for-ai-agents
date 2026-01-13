---
title: Evolutionary Architecture
source_url: practice.tech.evolutionary_arch.base/guidances/supportingmaterials/release_info_evolutionary_arch_FF1ACAA6.html
type: SupportingMaterial
uma_name: release_info_evolutionary_arch
page_guid: _rA1NMc3lEdyjXslGsagg_w
keywords:
- architecture
- evolutionary
---


---

Main Description

###  EPF base

####  1.5.1

Bugzilla 313572: Emphasized the agile nature of envisioning and modeling the architecture.  Other minor fixes.

####  1.5

This is the first version of this practice, included as part of the EPF 1.5 practices library. It is derived primarily from OpenUP 1.0 content, and it includes refinements to structure the content into a practice and clean up content to remove redundancy and improve consistency.  The following specific changes were made:
  * Created plug-ins and content packages to support practice library structure -- separate base and assign practice plug-ins, separate role definition plug-in, and so forth.
  * Implemented delayed role assignment. Placed Architect role in new role definition plug-in. Moved all role assignments and assignments of tasks and work products to standard categories to new assign plug-in.
  * Implemented default navigation view approach. Mapped all elements to the navigation view building blocks so that they are included in a view
  * Removed term definitions for roles and work products, because their definitions are enough.
  * Changed name of _Task: Outline the Architecture_ to _Task: Envision the Architecture_.
  * Changed the name of _Task: Refine the Architecture_ to _Task: Evolve the Architecture_.
  * Identified guidance that can be shared between architectural tasks and practices and defined the appropriate practice elements in the common architectural guidance package in a separate, common plug-in \(core.tech.common.base\).
  * Reviewed and re-factored tasks. Moved task details to guidance, where it can be shared between architectural tasks and practices.
  * Placed all content related to visual modeling in separate content package, both in the common plug-ins and in the practice plug-ins.
  * Created new elements that are common to all practices: Custom category with a description of "title page" for the practice, How to Adopt page, Release Info page, and so on.
  * Removed association with guidance from the architecture discipline. It is just a standard category. All guidance is associated with roles, tasks, work products \(or other guidance\).
  * Cleaned up the content to reflect the latest authoring guidelines:
  *     * Removed references to specific roles in all elements
    * Removed references to specific method assets \(for example, OpenUP\) and specific lifecycles \(such as RUP phases\) from the method element descriptions.
    * Replaced references to artifacts outside of the practice with references to the appropriate slots.
    * Eliminated redundancy among tasks, concepts, and guidance. In many cases, this led to the deletion of several guidance pages and the addition of several common guidance pages.

The following method elements were added:
  * Key concepts, so they can be shared:
    * Concept: Analysis Mechanism
    * Concept: Architectural Goals
    * Concept: Architectural Constraints
    * Concept: Architecturally Significant Requirements
    * Concept: Key Abstractions
    * Concept: Architectural Views and Viewpoints
  * Example: 4+1 Views of Software Architecture \(just renaming and retyping of original Guideline: Architectural View\)
  * Guideline: Representing Interfaces to External Systems \(defined to share content between the Concept: Software Architecture and the Task: Refine the Architecture\)
  * Guideline: Using Visual Modeling \(visual modeling was originally in an addendum to the Guideline: Abstract Away Complexity\)
  * Guideline: Modeling the Architecture \(information on visual architectural models\)
  * Practice elements \(elements common to all practices\):
  *     * Roadmap: How to Adopt This Practice
    * Custom Category: Evolutionary Architecture Practice
    * Supporting Material: Evolutionary Architecture Practice Release Information

The following are the method elements that were deleted:
  * Guideline: Architectural Mechanisms \(content merged with existing Concept: Architectural Mechanism to eliminate redundancy\)
  * Guideline: Determining Architecturally Significant Requirements \(content moved to new Concept: Architectural goals\)
  * Guideline: Architectural View \(replaced with new Example: 4+1 Views of Software Architecture\)
  * Guideline: Outline the Architecture \(content moved to more specific individual guidelines\)
  * Guideline: Develop the Architecture \(content moved to more specific individual guidelines
---
