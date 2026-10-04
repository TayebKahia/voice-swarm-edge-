#!/usr/bin/env python3
"""Inject speaker notes from SLIDES_AND_NOTES.md into a PPTX file using pure standard library zipfile & xml."""

import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def extract_notes_from_markdown(md_path):
    """Parses SLIDES_AND_NOTES.md and extracts slide number -> notes text."""
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Split by Slide header: e.g. "### Slide 1: ..."
    pattern = r'### Slide (\d+):[^\n]*\n(.*?)(?=\n### Slide \d+:|\Z)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    notes_dict = {}
    for num_str, content in matches:
        num = int(num_str)
        # Find Presenter Notes section
        notes_match = re.search(r'🗣️ Private Presenter Notes[^\n]*\n(.*?)(?=\n---|\Z)', content, re.DOTALL)
        if notes_match:
            raw_notes = notes_match.group(1).strip()
            # Clean markdown blockquotes and headers
            cleaned_lines = []
            for line in raw_notes.split('\n'):
                line = line.strip()
                if line.startswith('>'):
                    line = line.lstrip('>').strip()
                cleaned_lines.append(line)
            notes_dict[num] = '\n'.join(cleaned_lines).strip()
    return notes_dict

def inject_notes_into_pptx(input_pptx, output_pptx, notes_dict):
    """Injects notesSlides into a PPTX zip archive."""
    with zipfile.ZipFile(input_pptx, 'r') as zin:
        file_map = {item.filename: zin.read(item.filename) for item in zin.infolist()}

    # Determine existing slide numbers
    slide_files = sorted([f for f in file_map.keys() if re.match(r'^ppt/slides/slide\d+\.xml$', f)],
                         key=lambda x: int(re.search(r'slide(\d+)\.xml', x).group(1)))
    
    total_slides = len(slide_files)
    print(f"Found {total_slides} slides in {input_pptx}")

    # Read [Content_Types].xml
    content_types_str = file_map['[Content_Types].xml'].decode('utf-8')
    
    for i, slide_file in enumerate(slide_files, 1):
        note_text = notes_dict.get(i, f"Slide {i} Presenter Notes")
        
        # Build notesSlide XML
        # Escape XML entities in note_text
        paragraphs = note_text.split('\n\n')
        p_xml = ""
        for p in paragraphs:
            clean_p = p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            p_xml += f"""
          <a:p>
            <a:r>
              <a:rPr lang="en-US"/>
              <a:t>{clean_p}</a:t>
            </a:r>
          </a:p>"""

        notes_slide_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:notes xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
         xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
         xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Slide Image Placeholder"/>
          <p:cNvSpPr>
            <a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/>
          </p:cNvSpPr>
          <p:nvPr>
            <p:ph type="sldImg"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
      </p:sp>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="3" name="Notes Placeholder"/>
          <p:cNvSpPr>
            <a:spLocks noGrp="1"/>
          </p:cNvSpPr>
          <p:nvPr>
            <p:ph type="body" idx="1"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>{p_xml}
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:notes>"""

        notes_filename = f"ppt/notesSlides/notesSlide{i}.xml"
        file_map[notes_filename] = notes_slide_xml.encode('utf-8')

        # Add notesSlide rels
        notes_rels_filename = f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels"
        notes_rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../slides/slide{i}.xml"/>
</Relationships>"""
        file_map[notes_rels_filename] = notes_rels_xml.encode('utf-8')

        # Update slide rels
        slide_rel_filename = f"ppt/slides/_rels/slide{i}.xml.rels"
        if slide_rel_filename in file_map:
            slide_rels_str = file_map[slide_rel_filename].decode('utf-8')
            if 'notesSlide' not in slide_rels_str:
                # Add relationship
                insert_rel = f'<Relationship Id="rIdNotes{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide{i}.xml"/>'
                slide_rels_str = slide_rels_str.replace('</Relationships>', f'  {insert_rel}\n</Relationships>')
                file_map[slide_rel_filename] = slide_rels_str.encode('utf-8')
        else:
            slide_rels_str = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdNotes{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide{i}.xml"/>
</Relationships>"""
            file_map[slide_rel_filename] = slide_rels_str.encode('utf-8')

        # Update [Content_Types].xml
        override_entry = f'<Override PartName="/ppt/notesSlides/notesSlide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>'
        if override_entry not in content_types_str:
            content_types_str = content_types_str.replace('</Types>', f'  {override_entry}\n</Types>')

    file_map['[Content_Types].xml'] = content_types_str.encode('utf-8')

    # Write out new PPTX
    with zipfile.ZipFile(output_pptx, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for fname, data in file_map.items():
            zout.writestr(fname, data)
    print(f"Successfully wrote {output_pptx} with speaker notes injected into all {total_slides} slides.")

if __name__ == '__main__':
    md_file = Path('presentation/SLIDES_AND_NOTES.md')
    if not md_file.exists():
        print(f"Error: {md_file} not found.")
        sys.exit(1)
        
    notes = extract_notes_from_markdown(md_file)
    print(f"Extracted speaker notes for {len(notes)} slides from {md_file}")

    if len(sys.argv) >= 3:
        input_pptx = sys.argv[1]
        output_pptx = sys.argv[2]
        offset = int(sys.argv[3]) if len(sys.argv) >= 4 else 1
        # If offset > 1, shift the notes mapping
        offset_notes = {i: notes.get(i + offset - 1, f"Slide {i + offset - 1} Notes") for i in range(1, 100)}
        inject_notes_into_pptx(input_pptx, output_pptx, offset_notes)
    else:
        # Check defaults
        targets = [
            ('presentation/canva_block0_white_blue.pptx', 'presentation/canva_block0_white_blue_with_notes.pptx'),
            ('presentation/canva_block0_intro.pptx', 'presentation/canva_block0_intro_with_notes.pptx'),
            ('presentation/canva_defense_presentation.pptx', 'presentation/canva_defense_presentation_with_notes.pptx'),
        ]
        for inp, outp in targets:
            if Path(inp).exists():
                inject_notes_into_pptx(inp, outp, notes)
