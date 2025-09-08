import React, { useState } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Box,
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';

const ReportsPage = () => {
  const [reportType, setReportType] = useState('');
  const [deviceId, setDeviceId] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const reportTypes = [
    { value: 'summary', label: 'Summary Report' },
    { value: 'trip', label: 'Trip Report' },
    { value: 'stop', label: 'Stop Report' },
    { value: 'event', label: 'Event Report' },
    { value: 'chart', label: 'Chart Report' },
    { value: 'route', label: 'Route Report' }
  ];

  const handleGenerateReport = () => {
    // Logic to generate report
    console.log('Generating report:', { reportType, deviceId, dateFrom, dateTo });
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Reports
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Generate Report
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Report Type</InputLabel>
                <Select
                  value={reportType}
                  label="Report Type"
                  onChange={(e) => setReportType(e.target.value)}
                >
                  {reportTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Device ID"
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                placeholder="Enter device ID or leave empty for all devices"
              />

              <TextField
                fullWidth
                label="From Date"
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />

              <TextField
                fullWidth
                label="To Date"
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />

              <Button
                variant="contained"
                onClick={handleGenerateReport}
                disabled={!reportType}
                sx={{ mt: 2 }}
              >
                Generate Report
              </Button>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Reports
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button variant="outlined" fullWidth>
                  Today's Summary
                </Button>
                <Button variant="outlined" fullWidth>
                  Weekly Report
                </Button>
                <Button variant="outlined" fullWidth>
                  Monthly Report
                </Button>
                <Button variant="outlined" fullWidth>
                  Device Performance
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Report History
            </Typography>
            <Box 
              sx={{ 
                height: 200, 
                backgroundColor: '#f5f5f5', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                border: '2px dashed #ccc'
              }}
            >
              <Typography variant="body1" color="text.secondary">
                Generated reports will appear here
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ReportsPage;

