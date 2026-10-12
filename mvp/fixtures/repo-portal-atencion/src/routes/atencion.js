const express = require('express');
const router = express.Router();

router.get('/api/v1/atencion/tickets', (req, res) => {
  res.json({
    status: 'success',
    data: [
      { ticketId: 'TCK-2024-001', estado: 'EN_PROCESO', tipo: 'CONSULTA' }
    ]
  });
});

router.post('/api/v1/atencion/citas', (req, res) => {
  res.json({
    status: 'created',
    citaId: 'CTA-9081'
  });
});

module.exports = router;
