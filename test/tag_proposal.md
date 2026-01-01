# 标签 (Tags) Column Analysis & Proposal

## Current State Analysis

**Total Records**: 733
- Records with tags: 564 (77.0%)
- Records without tags: 169 (23.0%)
- Total tag instances: 575
- Unique tag values: 10

### Current Tag Values (sorted by frequency):

| Tag | Count | Issues |
|-----|-------|--------|
| `Doer` | 224 | ✅ Good |
| `Frontier` | 120 | ✅ Good (program-specific tag) |
| `Engineer / Lead` | 114 | ⚠️ Inconsistent format (slash) |
| `Investor` | 60 | ✅ Good |
| `Student` | 31 | ✅ Good |
| `Professor` | 14 | ✅ Good |
| `VP` | 6 | ⚠️ Too specific, might belong in Title field |
| `非会员` | 4 | ❌ Mixed language (Chinese) |
| `lawyer` | 1 | ❌ Inconsistent capitalization |
| `House Owner` | 1 | ❌ Out of place, unclear purpose |

## Issues Identified

1. **Inconsistent Capitalization**: `lawyer` vs `Doer`, `VP`, etc.
2. **Mixed Languages**: `非会员` (Chinese) mixed with English tags
3. **Inconsistent Formatting**: `Engineer / Lead` uses slash, others don't
4. **Overly Specific Tags**: `VP` is a job title, not a category tag
5. **Out-of-Place Tags**: `House Owner` doesn't fit the professional categorization
6. **Membership Status Confusion**: `非会员` should be in a separate "Membership Status" field, not tags

## Proposed Solution

### Recommended Tag Categories

The tags should represent **professional roles/categories** that help group people by their primary function or expertise area. Here's a cleaner, more standardized set:

#### **Core Professional Categories** (Primary Tags):

1. **`Founder`** - Entrepreneurs, startup founders, company creators
   - *Replaces/consolidates: "Doer" (which is vague)*
   
2. **`Frontier`** - Members of the Frontier program
   - *Keep as is (program-specific tag)*
   
3. **`Researcher`** - Research scientists, academics, researchers (not in Frontier program)
   - *New category for researchers outside the Frontier program*
   
4. **`Engineer`** - Software engineers, technical leads, engineering roles
   - *Replaces: "Engineer / Lead" (simplified, remove slash)*
   
5. **`Investor`** - VCs, angel investors, investment professionals
   - *Keep as is*
   
6. **`Academic`** - Professors, university faculty, academic researchers
   - *Replaces: "Professor" (more inclusive)*
   
7. **`Student`** - Current students, PhD candidates
   - *Keep as is*

#### **Additional Categories** (if needed):

8. **`Executive`** - C-level executives, VPs, senior management
   - *Consolidates: "VP" and other executive roles*
   
9. **`Professional`** - Other professional roles (lawyers, consultants, etc.)
   - *Replaces: "lawyer" (more general category)*

### Migration Plan

#### Step 1: Standardize Existing Tags

| Current Tag | Proposed New Tag | Notes |
|------------|------------------|-------|
| `Doer` | `Founder` | More descriptive and standard |
| `Frontier` | `Frontier` | Keep as is (program-specific) |
| `Engineer / Lead` | `Engineer` | Simplified, remove slash |
| `Investor` | `Investor` | Keep as is |
| `Student` | `Student` | Keep as is |
| `Professor` | `Academic` | More inclusive term |
| `VP` | `Executive` | More general category |
| `非会员` | **Remove** | Move to "Membership Status" field |
| `lawyer` | `Professional` | More general category |
| `House Owner` | **Remove** | Not a professional category |

#### Step 2: Handle Edge Cases

- **Multiple Tags**: Some records might need multiple tags (e.g., someone who is both a Founder and Investor)
  - **Solution**: Use Airtable's multi-select field type to allow multiple tags per record

#### Step 3: Clean Up Membership Status

- Move `非会员` to the existing "会员状态" (Membership Status) field
- Tags should only represent professional categories, not membership status

## Final Recommended Tag List

### Primary Tags (Single Select or Multi-Select):

1. **`Founder`** - Startup founders, entrepreneurs
2. **`Frontier`** - Members of the Frontier program
3. **`Researcher`** - Research scientists, R&D professionals (not in Frontier program)
4. **`Engineer`** - Software engineers, technical leads
5. **`Investor`** - VCs, angel investors
6. **`Academic`** - Professors, university faculty
7. **`Student`** - Current students
8. **`Executive`** - C-level, VPs, senior management
9. **`Professional`** - Other professional roles

### Benefits of This Approach:

✅ **Consistent capitalization** (all title case)
✅ **Single language** (English only)
✅ **Clear, descriptive names** (no vague terms like "Doer")
✅ **Standardized formatting** (no slashes or special characters)
✅ **Professional focus** (removes non-professional tags)
✅ **Scalable** (easy to add new categories if needed)
✅ **Better filtering** (clear categories for grouping and views)

## Implementation Notes

1. **Field Type**: Recommend using **Multi-select** field type to allow records to have multiple tags (e.g., someone can be both "Founder" and "Investor")

2. **Migration Script**: Create a script to:
   - Map old tags to new tags
   - Remove membership-related tags
   - Handle edge cases (multiple tags, empty tags)

3. **Validation**: Add validation to prevent:
   - Custom tag entries (use dropdown only)
   - Mixed languages
   - Non-standard formatting

