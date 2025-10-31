# TODO: Add Link Feature

## 1. Add Link Model
- [x] Add Link model to models.py with fields: id, name, url, course_id, created_at

## 2. Create Migration
- [x] Generate Alembic migration for Link model
- [x] Run migration to create links table

## 3. Add API Endpoint
- [x] Add POST /api/courses/<course_id>/links endpoint in blueprints/courses.py
- [x] Validate teacher permission, sanitize inputs, create link

## 4. Update Main Blueprint
- [x] Update course_detail route in blueprints/main.py to include links in topics list

## 5. Update Template
- [x] Add create-link-modal in course_detail.html similar to quiz modal
- [x] Update "Add File/Link" dropdown item to trigger modal
- [x] Update topics display to show links with target="_blank" and link icon
- [x] Add JavaScript for modal handling and form submission

## 6. Test Implementation
- [x] Test modal opens and closes
- [x] Test form submission creates link
- [x] Test link opens in new window
- [x] Verify topics list includes links
- [x] Test file upload and serving
