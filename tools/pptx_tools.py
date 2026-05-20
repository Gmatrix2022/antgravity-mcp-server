import win32com.client
import pythoncom
import traceback
from typing import Dict, Any, List

class PowerPointController:
    def __init__(self):
        # We must initialize COM for multi-threading environments
        pythoncom.CoInitialize()
        try:
            # Connect to existing PowerPoint application or start a new one
            self.app = win32com.client.Dispatch("PowerPoint.Application")
            self.app.Visible = True
        except Exception as e:
            raise Exception(f"Failed to connect to PowerPoint: {str(e)}")

    def get_active_presentation(self):
        if self.app.Presentations.Count == 0:
            raise Exception("No active presentation open in PowerPoint.")
        return self.app.ActivePresentation

    def read_slide(self, slide_index: int) -> Dict[str, Any]:
        """
        Reads all text shapes from a specific slide.
        slide_index is 1-based.
        """
        try:
            presentation = self.get_active_presentation()
            if slide_index < 1 or slide_index > presentation.Slides.Count:
                raise Exception(f"Slide index {slide_index} out of range (1 - {presentation.Slides.Count})")

            slide = presentation.Slides(slide_index)
            shapes_data = []

            for shape in slide.Shapes:
                if shape.HasTextFrame:
                    if shape.TextFrame.HasText:
                        shapes_data.append({
                            "id": shape.Id,
                            "name": shape.Name,
                            "type": shape.Type,
                            "text": shape.TextFrame.TextRange.Text.strip()
                        })

            return {
                "slide_index": slide_index,
                "shape_count": len(shapes_data),
                "shapes": shapes_data
            }
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def fill_text(self, slide_index: int, shape_id: int, new_text: str) -> Dict[str, Any]:
        """
        Fills a specific shape on a specific slide with new_text.
        """
        try:
            presentation = self.get_active_presentation()
            slide = presentation.Slides(slide_index)
            
            # Find the shape by ID
            target_shape = None
            for shape in slide.Shapes:
                if shape.Id == shape_id:
                    target_shape = shape
                    break
                    
            if not target_shape:
                raise Exception(f"Shape with ID {shape_id} not found on slide {slide_index}")
                
            if not target_shape.HasTextFrame:
                raise Exception(f"Shape with ID {shape_id} does not support text.")
                
            target_shape.TextFrame.TextRange.Text = new_text
            
            return {"success": True, "message": f"Successfully updated shape {shape_id}"}
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def create_slide(self, layout_index: int = 12) -> Dict[str, Any]:
        """
        Creates a new slide at the end of the presentation.
        layout_index 12 is typically ppLayoutBlank.
        """
        try:
            presentation = self.get_active_presentation()
            new_index = presentation.Slides.Count + 1
            slide = presentation.Slides.Add(new_index, layout_index)
            return {"success": True, "new_slide_index": new_index}
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def __del__(self):
        pythoncom.CoUninitialize()

# Testing functions directly if run as script
if __name__ == "__main__":
    controller = PowerPointController()
    print(controller.read_slide(1))
