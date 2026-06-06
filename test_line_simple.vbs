Sub CATMain()
    Dim partDoc
    Set partDoc = CATIA.ActiveDocument
    Dim part
    Set part = partDoc.Part

    ' Create sketch on XY plane
    Dim originElements
    Set originElements = part.OriginElements
    Dim xyPlane
    Set xyPlane = originElements.PlaneXY

    ' Create sketch
    Dim sketch
    Set sketch = part.MainBody.Sketches.Add(xyPlane)
    sketch.Name = "ShaftSketch"

    ' Open sketch and create circle + axis line
    Dim factory2D
    Set factory2D = sketch.OpenEdition()
    Dim circle2D
    Set circle2D = factory2D.CreateClosedCircle(50, 0, 15)
    
    ' Create axis line (this will be the rotation axis)
    Dim axisLine
    Set axisLine = factory2D.CreateLine(0, 0, 0, 100, 0)  ' Y-axis line
    axisLine.Name = "RotationAxis"
    
    ' Set the axis line as construction geometry
    axisLine.Construction = True
    
    sketch.CloseEdition

    ' Create shaft - the sketch contains the axis line
    Dim shaft
    Set shaft = part.ShapeFactory.AddNewShaft(sketch)
    
    ' Update
    part.Update
    MsgBox "Shaft created with axis line in sketch: " & shaft.Name
End Sub