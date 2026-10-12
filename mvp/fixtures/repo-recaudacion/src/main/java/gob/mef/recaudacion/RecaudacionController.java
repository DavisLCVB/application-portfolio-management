package gob.mef.recaudacion;

import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/recaudacion")
public class RecaudacionController {

    @GetMapping("/pagos")
    public List<Map<String, Object>> listarPagos() {
        return List.of(Map.of("id", "PAG-001", "monto", 1500.0, "estado", "CONFIRMADO"));
    }

    @PostMapping("/comprobantes")
    public Map<String, Object> emitirComprobante(@RequestBody Map<String, Object> payload) {
        return Map.of("comprobanteId", "CP-8899", "resultado", "EXITOSO");
    }
}
