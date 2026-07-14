#include <pybind11/pybind11.h>
#include <QString>
#include <QImage>
#include <QBuffer>
#include <QByteArray>

// Krita internal headers (requires Krita-dev / source tree to compile)
#include <KisResourceLocator.h>
#include <kis_paintop_preset.h>
#include <kis_painter.h>
#include <kis_paint_device.h>
#include <kis_paint_information.h>
#include <kis_distance_information.h>
#include <KoColorSpaceRegistry.h>
#include <KoColorSpace.h>

namespace py = pybind11;

py::bytes render_preview(const std::string& preset_name, int width, int height) {
    // 1. Get standard RGBA8 color space
    const KoColorSpace *cs = KoColorSpaceRegistry::instance()->rgb8();
    if (!cs) return py::bytes();
    
    // 2. Create memory paint device
    KisPaintDeviceSP device = new KisPaintDevice(cs);
    
    // 3. Locate the brush preset by name
    QString qPresetName = QString::fromStdString(preset_name);
    KoResourceSP res = KisResourceLocator::instance()->resourceForName(ResourceType::PaintOpPresets, qPresetName);
    if (!res) return py::bytes();
    
    KisPaintOpPresetSP preset = res.dynamicCast<KisPaintOpPreset>();
    if (!preset) return py::bytes();
    
    // 4. Setup Krita's internal painter
    KisPainter painter(device);
    painter.setPaintOpPreset(preset, nullptr);
    
    // 5. Draw a simple curved line mimicking a stroke
    KisDistanceInformation dist;
    int steps = 25;
    QPointF start(width * 0.1, height * 0.5);
    QPointF end(width * 0.9, height * 0.5);
    
    QPointF prevPoint = start;
    for (int i = 1; i <= steps; ++i) {
        float t = (float)i / steps;
        float x = start.x() + (end.x() - start.x()) * t;
        float y = start.y() + 15.0 * sin(t * 3.14159 * 2.0); // Sine wave curve
        
        QPointF nextPoint(x, y);
        KisPaintInformation pi1(prevPoint);
        KisPaintInformation pi2(nextPoint);
        
        painter.paintLine(pi1, pi2, &dist);
        prevPoint = nextPoint;
    }
    
    // 6. Convert device to QImage (extract rect 0, 0, width, height)
    QImage image = device->convertToQImage(nullptr, 0, 0, width, height);
    
    // 7. Serialize to PNG format for Python
    QByteArray arr;
    QBuffer buffer(&arr);
    buffer.open(QIODevice::WriteOnly);
    image.save(&buffer, "PNG");
    
    return py::bytes(arr.constData(), arr.size());
}

PYBIND11_MODULE(brush_studio_engine, m) {
    m.doc() = "Brush Studio C++ Engine for Krita";
    m.def("render_preview", &render_preview, 
          "Render a brush preset stroke to PNG bytes in memory",
          py::arg("preset_name"), py::arg("width") = 384, py::arg("height") = 128);
}
