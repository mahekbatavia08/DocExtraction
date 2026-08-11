import React, { useState, useMemo } from 'react';
import { Building, Search, Download, Trash2, Copy, AlertTriangle, Play, CheckCircle, Clock } from 'lucide-react';
import { Box, Card, CardContent, Typography, Button, IconButton, TextField, Table, TableBody, TableCell, TableHead, TableRow, Chip, Dialog, DialogTitle, DialogContent, DialogActions, Tooltip, Snackbar, Alert, LinearProgress } from '@mui/material';
import { DocumentOCRModule, QueueItem } from '../components/DocumentOCRModule';
import { parseBusinessCard } from '../utils/documentExtractors';
import { CardDetailModal } from '../components/CardDetailModal';

export interface Contact {
  id: string;
  name: string;
  company: string;
  email: string;
  phone: string;
  queueItem: QueueItem;
}

export const BusinessCardPage: React.FC = () => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [search, setSearch] = useState('');
  const [sortField, setSortField] = useState<'name' | 'company' | 'date'>('date');
  
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  
  // Duplicate detection state
  const [duplicateAlert, setDuplicateAlert] = useState<{ open: boolean; newContact: Contact; existingContact: Contact } | null>(null);

  const [toast, setToast] = useState<{ open: boolean; message: string; severity: 'success' | 'info' | 'warning' }>({ open: false, message: '', severity: 'info' });

  const showToast = (message: string, severity: 'success' | 'info' | 'warning' = 'success') => setToast({ open: true, message, severity });

  const handleItemCompleted = (item: QueueItem) => {
    if (!item.specializedFields) return;
    const f = item.specializedFields;
    const newContact: Contact = {
      id: item.id,
      name: f['Name'] || '',
      company: f['Company'] || '',
      email: f['Email'] || '',
      phone: f['Phone'] || '',
      queueItem: item
    };

    // Check duplicates based on user instructions (Email, Phone, Company)
    const isDuplicate = contacts.find(c => 
      (c.email && c.email.toLowerCase() === newContact.email.toLowerCase()) || 
      (c.phone && c.phone === newContact.phone) || 
      (c.company && c.name && c.company.toLowerCase() === newContact.company.toLowerCase() && c.name.toLowerCase() === newContact.name.toLowerCase())
    );

    if (isDuplicate) {
      setDuplicateAlert({ open: true, newContact, existingContact: isDuplicate });
    } else {
      setContacts(prev => [...prev, newContact]);
      showToast('Contact Added');
    }
  };

  const handleDuplicateAction = (action: 'keep' | 'update' | 'skip') => {
    if (!duplicateAlert) return;
    const { newContact, existingContact } = duplicateAlert;
    
    if (action === 'keep') {
      setContacts(prev => [...prev, newContact]);
      showToast('Both contacts kept');
    } else if (action === 'update') {
      setContacts(prev => prev.map(c => c.id === existingContact.id ? { ...newContact, id: existingContact.id } : c));
      showToast('Contact updated');
    } else {
      showToast('Duplicate skipped', 'info');
    }
    setDuplicateAlert(null);
  };

  const handleCopy = (e: React.MouseEvent, text: string) => {
    e.stopPropagation();
    if (!text) return;
    navigator.clipboard.writeText(text);
    showToast('Copied to clipboard');
  };

  const exportVCard = (contactList: Contact[]) => {
    let vcf = '';
    contactList.forEach(c => {
      vcf += 'BEGIN:VCARD\nVERSION:3.0\n';
      vcf += `FN:${c.name}\n`;
      if (c.company) vcf += `ORG:${c.company}\n`;
      if (c.email) vcf += `EMAIL:${c.email}\n`;
      if (c.phone) vcf += `TEL:${c.phone}\n`;
      vcf += 'END:VCARD\n';
    });
    
    const blob = new Blob([vcf], { type: 'text/vcard' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `contacts_export_${Date.now()}.vcf`;
    link.click();
    URL.revokeObjectURL(url);
    showToast('Exported to vCard');
  };

  const filteredContacts = useMemo(() => {
    let result = [...contacts];
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(c => 
        c.name.toLowerCase().includes(q) || 
        c.company.toLowerCase().includes(q) || 
        c.email.toLowerCase().includes(q) ||
        c.phone.includes(q)
      );
    }
    
    if (sortField === 'name') result.sort((a, b) => a.name.localeCompare(b.name));
    else if (sortField === 'company') result.sort((a, b) => a.company.localeCompare(b.company));
    
    return result;
  }, [contacts, search, sortField]);

  const renderCustomBatchView = (
    queue: QueueItem[], 
    actions: { handleClearAll: () => void, startProcessingQueue: () => void, isProcessingQueue: boolean, setQueue: any }
  ) => {
    return (
      <Card sx={{ borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <CardContent sx={{ p: 0 }}>
           <Box sx={{ p: 3, background: 'rgba(0,0,0,0.2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
             <Box>
                <Typography variant="h6" sx={{ fontWeight: 800, color: '#10b981', display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Building size={20} /> Contact Manager
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  {queue.filter(q => q.status === 'waiting').length} Waiting | {contacts.length} Contacts
                </Typography>
             </Box>
             
             <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <TextField 
                  size="small" 
                  placeholder="Search contacts..." 
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  InputProps={{ startAdornment: <Search size={16} color="#94a3b8" style={{ marginRight: 8 }} /> }}
                  sx={{ width: 200 }}
                />
                <Button variant="outlined" size="small" onClick={() => setSortField(prev => prev === 'name' ? 'company' : (prev === 'company' ? 'date' : 'name'))} sx={{ borderRadius: '8px' }}>
                  Sort: {sortField.toUpperCase()}
                </Button>
                
                <Button variant="contained" color="success" disabled={actions.isProcessingQueue || queue.filter(q => q.status === 'waiting').length === 0} onClick={actions.startProcessingQueue} startIcon={<Play size={16} />} sx={{ borderRadius: '8px', fontWeight: 600 }}>
                  {actions.isProcessingQueue ? 'Processing...' : 'Process Queue'}
                </Button>
                
                <Button variant="outlined" color="primary" disabled={filteredContacts.length === 0} onClick={() => exportVCard(filteredContacts)} startIcon={<Download size={16} />} sx={{ borderRadius: '8px' }}>
                  Export vCard
                </Button>
                <Button variant="outlined" color="error" disabled={actions.isProcessingQueue} onClick={() => { actions.handleClearAll(); setContacts([]); }} startIcon={<Trash2 size={16} />} sx={{ borderRadius: '8px' }}>
                  Clear All
                </Button>
             </Box>
           </Box>

           <Box sx={{ overflowX: 'auto' }}>
             <Table size="small">
               <TableHead>
                 <TableRow sx={{ background: 'rgba(255, 255, 255, 0.03)' }}>
                   <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Name</TableCell>
                   <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Company</TableCell>
                   <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Phone</TableCell>
                   <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Email</TableCell>
                   <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }} align="right">Actions</TableCell>
                 </TableRow>
               </TableHead>
               <TableBody>
                 {filteredContacts.map((contact) => (
                   <TableRow 
                     key={contact.id} 
                     hover 
                     onClick={() => setSelectedContact(contact)}
                     sx={{ cursor: 'pointer', transition: 'background 0.2s', '&:hover': { background: 'rgba(16, 185, 129, 0.05)' } }}
                   >
                     <TableCell sx={{ fontWeight: 600 }}>{contact.name || '-'}</TableCell>
                     <TableCell>{contact.company || '-'}</TableCell>
                     <TableCell>
                       <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                         {contact.phone || '-'}
                         {contact.phone && (
                           <Tooltip title="Copy Phone">
                             <IconButton size="small" onClick={(e) => handleCopy(e, contact.phone)}><Copy size={12} /></IconButton>
                           </Tooltip>
                         )}
                       </Box>
                     </TableCell>
                     <TableCell>
                       <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                         {contact.email || '-'}
                         {contact.email && (
                           <Tooltip title="Copy Email">
                             <IconButton size="small" onClick={(e) => handleCopy(e, contact.email)}><Copy size={12} /></IconButton>
                           </Tooltip>
                         )}
                       </Box>
                     </TableCell>
                     <TableCell align="right">
                       <Chip label="View Card" size="small" variant="outlined" color="success" onClick={(e) => { e.stopPropagation(); setSelectedContact(contact); }} sx={{ cursor: 'pointer' }} />
                     </TableCell>
                   </TableRow>
                 ))}
                 
                 {/* Processing or waiting items from the queue */}
                 {queue.filter(q => q.status === 'processing' || q.status === 'waiting').map((item, idx) => (
                   <TableRow key={item.id} sx={{ opacity: 0.7 }}>
                     <TableCell colSpan={2} sx={{ fontWeight: 600, color: 'text.secondary' }}>
                       {item.status === 'waiting' && <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}><Clock size={14}/> {item.fileName} (Waiting)</Box>}
                       {item.status === 'processing' && <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', color: '#3b82f6' }}><Play size={14} className="animate-pulse"/> {item.fileName} (Processing)</Box>}
                     </TableCell>
                     <TableCell colSpan={3}>
                       {item.status === 'processing' && <LinearProgress sx={{ mt: 1 }} />}
                     </TableCell>
                   </TableRow>
                 ))}
                 
                 {filteredContacts.length === 0 && queue.length === 0 && (
                   <TableRow>
                     <TableCell colSpan={5} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                       No contacts yet. Upload business cards to get started.
                     </TableCell>
                   </TableRow>
                 )}
               </TableBody>
             </Table>
           </Box>
        </CardContent>
      </Card>
    );
  };

  return (
    <>
      <DocumentOCRModule
        title="Business Card OCR"
        description="Extract Name, Company, Designation, Phone, Email, Website, and Address from visiting cards. Automatically build and export a contact list."
        badgeLabel="Contact Manager"
        badgeColor="success"
        icon={<Building size={28} color="#10b981" />}
        parseSpecializedFields={parseBusinessCard}
        onItemCompleted={handleItemCompleted}
        renderCustomBatchView={renderCustomBatchView}
      />

      <Snackbar open={toast.open} autoHideDuration={3000} onClose={() => setToast(prev => ({ ...prev, open: false }))} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={() => setToast(prev => ({ ...prev, open: false }))} severity={toast.severity} sx={{ width: '100%', borderRadius: '8px' }}>
          {toast.message}
        </Alert>
      </Snackbar>

      {/* Duplicate Alert Dialog */}
      <Dialog open={!!duplicateAlert} onClose={() => handleDuplicateAction('skip')} PaperProps={{ sx: { background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 3 } }}>
        <DialogTitle sx={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: 1 }}>
          <AlertTriangle size={20} /> Duplicate Contact Detected
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
            A contact with similar details already exists in your Contact Manager.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mb: 1 }}>
            <Box sx={{ flex: 1, p: 2, borderRadius: 2, background: 'rgba(0,0,0,0.3)' }}>
              <Typography variant="caption" color="text.secondary">Existing Contact</Typography>
              <Typography variant="body2" fontWeight={700}>{duplicateAlert?.existingContact.name}</Typography>
              <Typography variant="body2">{duplicateAlert?.existingContact.company}</Typography>
              <Typography variant="body2">{duplicateAlert?.existingContact.email}</Typography>
            </Box>
            <Box sx={{ flex: 1, p: 2, borderRadius: 2, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)' }}>
              <Typography variant="caption" color="text.secondary">New Scan</Typography>
              <Typography variant="body2" fontWeight={700}>{duplicateAlert?.newContact.name}</Typography>
              <Typography variant="body2">{duplicateAlert?.newContact.company}</Typography>
              <Typography variant="body2">{duplicateAlert?.newContact.email}</Typography>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => handleDuplicateAction('skip')} color="inherit">Skip</Button>
          <Button onClick={() => handleDuplicateAction('keep')} color="primary">Keep Both</Button>
          <Button onClick={() => handleDuplicateAction('update')} variant="contained" color="success">Update Existing</Button>
        </DialogActions>
      </Dialog>
      
      {/* Card Detail Modal */}
      {selectedContact && (
         <CardDetailModal 
           open={!!selectedContact} 
           onClose={() => setSelectedContact(null)} 
           cardResult={{
             ...selectedContact.queueItem.ocrResult,
             fields: selectedContact.queueItem.specializedFields,
             metadata: { document_type: 'Business Card', image_size: selectedContact.queueItem.ocrResult?.image_size },
             bounding_boxes: selectedContact.queueItem.ocrResult?.results
           }} 
           fileName={selectedContact.queueItem.fileName} 
         />
       )}
    </>
  );
};
