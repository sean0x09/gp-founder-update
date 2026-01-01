# Airtable Table Organization Recommendations

## Current State Summary
- **Total Records**: 737
- **Missing Bios**: 478 (64.9%)
- **Duplicate Names**: 13 people
- **Data Quality Issues**: Invalid URLs, placeholder values, mixed languages

---

## 1. FIELD NAMING STANDARDIZATION

### Recommendation: Standardize to English field names
**Current Issues:**
- Mixed Chinese/English field names make it hard for international team members
- Inconsistent naming conventions

**Suggested Field Name Mapping:**
```
您的姓名 → Name (Full Name)
别名/英文名 → English Name / Alias
Title → Job Title (or keep as Title)
目前就职 → Current Company
毕业院校 → Alma Mater / University
最高学历 → Highest Education
性别 → Gender
会员状态 → Membership Status
建联状态 → Connection Status
熟悉程度 → Relationship Level
参与活动次数 → Event Participation Count
标签 → Tags
Base → Location / Base Location
Profiles → LinkedIn Profile / Social Profiles
Profile Picture → Profile Photo
Bio → Bio (keep as is)
```

**Benefits:**
- Easier for international collaboration
- Better API integration
- More professional appearance
- Easier to maintain

---

## 2. DATA QUALITY IMPROVEMENTS

### A. Clean Invalid Profile URLs
**Issue**: Many records have "http:///" as Profile URL

**Action Items:**
1. Create a script to identify all invalid URLs
2. Either remove invalid URLs or mark them for manual review
3. Add validation to prevent future invalid entries

### B. Standardize Placeholder Values
**Issue**: Fields contain "Unknown", "not started", "Undisclosed"

**Recommendations:**
- Replace "Unknown" with empty/null values
- Create a status field for "not started" companies
- Use consistent values: "Undisclosed" → "Not Disclosed" or empty

### C. Resolve Duplicate Records
**Issue**: 13 people have duplicate entries

**Action Items:**
1. Create a deduplication script to identify duplicates
2. Merge duplicate records (keep most complete record)
3. Add unique constraint or validation on Name field

---

## 3. FIELD STRUCTURE IMPROVEMENTS

### A. Base/Location Field
**Current**: List field with values like ['China'], ['Bay Area', 'US']

**Recommendation**: Split into two fields:
- **Primary Location** (single select): Country/Region
- **Secondary Location** (single select): City/Area (optional)

**Benefits:**
- Easier filtering and grouping
- Better for geographic analysis
- More structured data

### B. Profiles Field
**Current**: Single string field

**Recommendation**: Split into separate fields:
- **LinkedIn URL** (URL field type)
- **Twitter/X URL** (URL field type)
- **Other Profiles** (text field for additional links)

**Benefits:**
- Better validation
- Easier to extract specific profile types
- Cleaner data structure

### C. Education Fields
**Current**: Separate fields for "毕业院校" and "最高学历"

**Recommendation**: Consider a linked table or formula field:
- **Education** (linked table) with fields:
  - Institution Name
  - Degree Type
  - Field of Study
  - Graduation Year
  - Is Highest Degree (checkbox)

**Benefits:**
- Support multiple degrees
- More detailed education tracking
- Better for filtering by education level

---

## 4. MISSING DATA PRIORITIZATION

### High Priority (Fill First):
1. **Bio** (64.9% missing) - Critical for profiles
2. **Profile Picture** (36.1% missing) - Important for visual identification
3. **Title** (4.3% missing) - Essential professional info

### Medium Priority:
1. **别名/英文名** (81.4% missing) - Useful but not critical
2. **参与活动次数** (76.0% missing) - Nice to have for engagement tracking

### Low Priority:
1. **性别** (23.3% missing) - May not be necessary depending on use case

---

## 5. FIELD GROUPING & VIEWS

### Recommended View Structure:

#### View 1: "All Members - Complete"
- Filter: All records with Name, Title, Company, Bio, Profile Picture
- Sort: By Name
- Use for: Main directory view

#### View 2: "Missing Bios"
- Filter: Bio is empty
- Sort: By Name
- Use for: Bio generation workflow

#### View 3: "By Location"
- Group by: Base/Location
- Sort: By Name within groups
- Use for: Geographic organization

#### View 4: "By Membership Status"
- Group by: 会员状态
- Sort: By Name within groups
- Use for: Membership management

#### View 5: "By Tag"
- Group by: 标签
- Sort: By Name within groups
- Use for: Role-based filtering

#### View 6: "Needs Review"
- Filter: Invalid URLs OR duplicates OR placeholder values
- Use for: Data cleanup tasks

---

## 6. DATA VALIDATION RULES

### Recommended Validations:

1. **Name Field**:
   - Required field
   - No duplicates (or flag duplicates)

2. **Profile URLs**:
   - Must be valid URL format
   - LinkedIn URLs should start with "https://www.linkedin.com/in/"

3. **Email/Contact** (if added):
   - Valid email format

4. **Education Level**:
   - Single select dropdown: "Below Bachelor", "Bachelor", "Master", "PhD"

---

## 7. ADDITIONAL FIELDS TO CONSIDER

### Recommended New Fields:

1. **Email** (Email field type)
   - For direct contact
   - Currently missing from structure

2. **Phone** (Phone number field type)
   - Optional contact method

3. **Last Updated** (Last modified time)
   - Auto-track when record was last modified
   - Useful for data freshness tracking

4. **Bio Generated Date** (Date field)
   - Track when bio was auto-generated
   - Helps identify stale bios

5. **Data Quality Score** (Formula field)
   - Calculate completeness percentage
   - Helps prioritize records for completion

6. **Company Type** (Single select)
   - Startup, VC, Corporate, etc.
   - Better than inferring from company name

---

## 8. IMPLEMENTATION PRIORITY

### Phase 1 (Immediate):
1. ✅ Resolve duplicate records
2. ✅ Clean invalid Profile URLs
3. ✅ Standardize placeholder values
4. ✅ Generate missing Bios (64.9% of records)

### Phase 2 (Short-term):
1. Standardize field names to English
2. Split Base field into Primary/Secondary Location
3. Split Profiles into separate fields
4. Create recommended views

### Phase 3 (Long-term):
1. Restructure Education fields (if needed)
2. Add new recommended fields
3. Set up data validation rules
4. Create automation for data quality monitoring

---

## 9. AUTOMATION OPPORTUNITIES

### Scripts to Create:

1. **Deduplication Script**
   - Identify and merge duplicate records
   - Keep most complete record

2. **URL Validation Script**
   - Check all Profile URLs
   - Flag invalid entries
   - Attempt to fix common issues

3. **Bio Generation Script** (already exists, but needs to run for all 478 missing)
   - Generate bios for all records missing Bio field
   - Use existing bio_generator.py as base

4. **Data Quality Report Script**
   - Generate weekly report on data completeness
   - Identify records needing attention

---

## 10. METRICS TO TRACK

### Key Metrics:
- **Data Completeness**: % of records with all critical fields filled
- **Bio Coverage**: % of records with Bio (target: 95%+)
- **Duplicate Rate**: Number of duplicate records (target: 0)
- **Invalid URL Rate**: % of invalid Profile URLs (target: <1%)
- **Last Updated**: Average days since last record update

---

## Summary

**Immediate Actions:**
1. Clean up 13 duplicate records
2. Fix invalid Profile URLs (http:///)
3. Generate bios for 478 missing records
4. Standardize placeholder values

**Quick Wins:**
- Create filtered views for common use cases
- Add data quality tracking fields
- Set up basic validation rules

**Long-term Improvements:**
- Standardize all field names to English
- Restructure multi-value fields (Base, Profiles)
- Add new fields for better data capture
- Implement automation for data quality

