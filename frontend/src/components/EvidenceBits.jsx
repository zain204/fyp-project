import { File, FileImage, FileText, FileVideo, FileArchive, Mail, FileAudio } from 'lucide-react'

export function fileIcon(mime = '', name = '') {
  const m = (mime || '').toLowerCase(), n = name.toLowerCase()
  if (m.startsWith('image/')) return FileImage
  if (m.startsWith('video/')) return FileVideo
  if (m.startsWith('audio/')) return FileAudio
  if (m.includes('pdf') || m.startsWith('text/') || n.endsWith('.txt') || n.endsWith('.docx')) return FileText
  if (n.endsWith('.eml') || n.endsWith('.msg') || m.includes('message')) return Mail
  if (m.includes('zip') || m.includes('compressed') || n.endsWith('.zip')) return FileArchive
  return File
}

export const FileGlyph = ({ mime, name, size = 18 }) => {
  const I = fileIcon(mime, name)
  return <span className="file-glyph"><I size={size} strokeWidth={1.5} /></span>
}

// Reads the backend's recorded status. is_verified is true at upload and is updated by each verify run.
export const verificationOf = (ev) => (ev.is_verified ? 'verified' : 'mismatch')
