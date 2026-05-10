import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useStore, { API_BASE } from '../store';

function formatDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric'
  });
}

function getFileIcon(filename) {
  const ext = (filename || '').split('.').pop()?.toLowerCase();
  if (ext === 'pdf') return 'picture_as_pdf';
  if (ext === 'docx' || ext === 'doc') return 'description';
  if (ext === 'txt') return 'article';
  return 'draft';
}

export default function DashboardPage() {
  const { user, documents, documentsLoading, fetchDocuments, token } = useStore();
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (documents.length === 0) {
      fetchDocuments();
    }
  }, []);

  const handleUpload = async (file) => {
    if (!file) return;
    setUploadError('');
    setUploadSuccess('');
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_BASE}/api/documents/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload thất bại');
      setUploadSuccess(`✅ Đã upload "${file.name}" thành công!`);
      await fetchDocuments(true);
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (e, docId) => {
    e.stopPropagation();
    if (!confirm('Xoá tài liệu này? Hành động không thể hoàn tác.')) return;
    setDeletingId(docId);
    try {
      const res = await fetch(`${API_BASE}/api/documents/${docId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok && res.status !== 204) throw new Error('Xoá thất bại');
      await fetchDocuments(true);
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) handleUpload(file);
  };

  const displayName = user?.email ? user.email.split('@')[0] : 'Student';

  return (
    <>
      <section className="mt-sm">
        <h2 className="font-h2 text-h2 text-primary mb-sm">Welcome back, {displayName}</h2>
        <p className="font-body-md text-body-md text-on-surface-variant mb-md">Upload tài liệu và để AI tạo Quiz & Flashcard cho bạn.</p>
        
        {/* Alerts */}
        {uploadError && (
          <div className="bg-error-container text-on-error-container p-sm rounded-xl mb-md border border-error/20 flex items-center gap-2">
            <span className="material-symbols-outlined">error</span>
            {uploadError}
          </div>
        )}
        {uploadSuccess && (
          <div className="bg-[#e6f4ea] text-[#16a34a] p-sm rounded-xl mb-md border border-[#16a34a]/20 flex items-center gap-2">
            <span className="material-symbols-outlined">check_circle</span>
            {uploadSuccess}
          </div>
        )}

        {/* Upload Zone */}
        <div
          className={`bg-surface-container-lowest rounded-xl shadow-ambient p-xl flex flex-col items-center justify-center gap-md border-2 border-dashed transition-all cursor-pointer ${dragging ? 'border-secondary bg-surface-container-low' : 'border-outline-variant/50 hover:border-secondary hover:bg-surface-container-low'}`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <div className="w-16 h-16 rounded-full bg-surface-container-high flex items-center justify-center text-secondary mb-sm">
            {uploading 
              ? <span className="material-symbols-outlined animate-spin text-[32px]">sync</span>
              : <span className="material-symbols-outlined text-[32px]">cloud_upload</span>
            }
          </div>
          <h3 className="font-h3 text-h3 text-primary text-center">
            {uploading ? 'Đang tải lên...' : 'Kéo thả hoặc click để upload'}
          </h3>
          <p className="font-body-md text-body-md text-on-surface-variant text-center">Hỗ trợ PDF, DOCX, TXT &middot; Tối đa 10MB</p>
          <button 
            className="mt-sm bg-secondary text-on-secondary font-button text-button px-md py-sm rounded-xl shadow-md hover:-translate-y-0.5 transition-all active:translate-y-0"
            disabled={uploading}
            onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
          >
            Chọn file
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>
      </section>

      {/* Documents List */}
      <section>
        <div className="flex justify-between items-center mb-sm">
          <h3 className="font-h3 text-h3 text-primary">Tài liệu của bạn</h3>
        </div>
        
        <div className="flex flex-col gap-sm">
          {documentsLoading && documents.length === 0 ? (
            <div className="flex justify-center p-xl">
              <span className="material-symbols-outlined animate-spin text-secondary text-4xl">sync</span>
            </div>
          ) : documents.length === 0 ? (
            <div className="bg-surface-container-lowest rounded-xl shadow-ambient p-xl border border-outline-variant/20 flex flex-col items-center gap-sm text-center">
              <span className="material-symbols-outlined text-outline-variant text-[48px]">description</span>
              <h4 className="font-button text-button text-on-background">Chưa có tài liệu nào</h4>
              <p className="font-body-md text-body-md text-on-surface-variant">Upload tài liệu đầu tiên của bạn để bắt đầu học!</p>
            </div>
          ) : (
            documents.map((doc) => {
              const name = doc.file_name || doc.filename || 'Tài liệu';
              const icon = getFileIcon(name);
              
              return (
                <div 
                  key={doc.id}
                  className="bg-surface-container-lowest rounded-xl shadow-ambient p-sm border border-outline-variant/20 flex items-center justify-between hover:border-secondary transition-all cursor-pointer group"
                  onClick={() => navigate(`/documents/${doc.id}`)}
                >
                  <div className="flex items-center gap-md truncate">
                    <div className="w-12 h-12 rounded-lg bg-surface-container flex items-center justify-center text-secondary group-hover:bg-secondary-container group-hover:text-on-secondary-container transition-colors shrink-0">
                      <span className="material-symbols-outlined text-[24px]">{icon}</span>
                    </div>
                    <div className="flex flex-col truncate">
                      <span className="font-button text-button text-on-background truncate">{name}</span>
                      <div className="flex items-center gap-xs mt-1">
                        <span className="font-label-caps text-label-caps text-on-surface-variant flex items-center gap-1">
                          <span className="material-symbols-outlined text-[14px]">schedule</span>
                          {formatDate(doc.created_at)}
                        </span>
                        {doc.status && doc.status !== 'ready' && (
                          <span className="font-label-caps text-label-caps px-2 py-0.5 rounded-full bg-error-container text-error ml-2">
                            {doc.status}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-xs shrink-0 ml-md">
                    <button 
                      className="w-10 h-10 rounded-full flex items-center justify-center text-secondary hover:bg-secondary-container/20 transition-colors"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/documents/${doc.id}`);
                      }}
                      title="Mở"
                    >
                      <span className="material-symbols-outlined">visibility</span>
                    </button>
                    <button 
                      className="w-10 h-10 rounded-full flex items-center justify-center text-error hover:bg-error-container/50 transition-colors"
                      onClick={(e) => handleDelete(e, doc.id)}
                      disabled={deletingId === doc.id}
                      title="Xoá"
                    >
                      {deletingId === doc.id ? (
                        <span className="material-symbols-outlined animate-spin">sync</span>
                      ) : (
                        <span className="material-symbols-outlined">delete</span>
                      )}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </section>
    </>
  );
}
