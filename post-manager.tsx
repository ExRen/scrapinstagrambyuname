import React, { useState } from 'react';
import { Upload, Download, FileText, Link, Calendar } from 'lucide-react';
import * as XLSX from 'xlsx';

export default function PostManager() {
  const [urlFiles, setUrlFiles] = useState([]);
  const [captionFiles, setCaptionFiles] = useState([]);
  const [tableData, setTableData] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const readFileContent = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const extractDateFromFilename = (filename) => {
    // Menghapus ekstensi .txt dan mengembalikan nama file sebagai identifier
    return filename.replace('.txt', '');
  };

  const handleUrlUpload = (e) => {
    const files = Array.from(e.target.files);
    setUrlFiles(files);
  };

  const handleCaptionUpload = (e) => {
    const files = Array.from(e.target.files);
    setCaptionFiles(files);
  };

  const processFiles = async () => {
    if (urlFiles.length === 0 || captionFiles.length === 0) {
      alert('Silakan upload file URL dan Caption terlebih dahulu');
      return;
    }

    setIsProcessing(true);

    try {
      // Baca semua file URL
      const urlData = {};
      for (const file of urlFiles) {
        const content = await readFileContent(file);
        const identifier = extractDateFromFilename(file.name);
        urlData[identifier] = content.trim();
      }

      // Baca semua file Caption
      const captionData = {};
      for (const file of captionFiles) {
        const content = await readFileContent(file);
        const identifier = extractDateFromFilename(file.name);
        captionData[identifier] = content.trim();
      }

      // Gabungkan data berdasarkan identifier
      const mergedData = [];
      const allIdentifiers = new Set([
        ...Object.keys(urlData),
        ...Object.keys(captionData)
      ]);

      allIdentifiers.forEach(identifier => {
        mergedData.push({
          tanggal: identifier,
          url: urlData[identifier] || '-',
          caption: captionData[identifier] || '-'
        });
      });

      // Urutkan berdasarkan tanggal (identifier)
      mergedData.sort((a, b) => a.tanggal.localeCompare(b.tanggal));

      setTableData(mergedData);
    } catch (error) {
      console.error('Error processing files:', error);
      alert('Terjadi kesalahan saat memproses file');
    } finally {
      setIsProcessing(false);
    }
  };

  const exportToExcel = () => {
    if (tableData.length === 0) {
      alert('Tidak ada data untuk di-export');
      return;
    }

    const worksheet = XLSX.utils.json_to_sheet(tableData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Postingan');

    // Set column widths
    worksheet['!cols'] = [
      { wch: 20 }, // Tanggal
      { wch: 50 }, // URL
      { wch: 80 }  // Caption
    ];

    XLSX.writeFile(workbook, `postingan_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2 flex items-center gap-3">
            <FileText className="text-indigo-600" />
            Pengelola URL & Caption Postingan
          </h1>
          <p className="text-gray-600 mb-6">Upload file TXT URL dan Caption untuk menampilkan dalam tabel</p>

          <div className="grid md:grid-cols-2 gap-6 mb-6">
            {/* Upload URL Files */}
            <div className="border-2 border-dashed border-indigo-300 rounded-xl p-6 hover:border-indigo-500 transition-colors">
              <label className="cursor-pointer block">
                <div className="flex flex-col items-center gap-3">
                  <Link className="w-12 h-12 text-indigo-600" />
                  <span className="font-semibold text-gray-700">Upload File URL</span>
                  <span className="text-sm text-gray-500">Format: tanggal.txt</span>
                  <input
                    type="file"
                    multiple
                    accept=".txt"
                    onChange={handleUrlUpload}
                    className="hidden"
                  />
                  {urlFiles.length > 0 && (
                    <span className="text-sm text-indigo-600 font-medium">
                      {urlFiles.length} file dipilih
                    </span>
                  )}
                </div>
              </label>
            </div>

            {/* Upload Caption Files */}
            <div className="border-2 border-dashed border-green-300 rounded-xl p-6 hover:border-green-500 transition-colors">
              <label className="cursor-pointer block">
                <div className="flex flex-col items-center gap-3">
                  <FileText className="w-12 h-12 text-green-600" />
                  <span className="font-semibold text-gray-700">Upload File Caption</span>
                  <span className="text-sm text-gray-500">Format: tanggal.txt</span>
                  <input
                    type="file"
                    multiple
                    accept=".txt"
                    onChange={handleCaptionUpload}
                    className="hidden"
                  />
                  {captionFiles.length > 0 && (
                    <span className="text-sm text-green-600 font-medium">
                      {captionFiles.length} file dipilih
                    </span>
                  )}
                </div>
              </label>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={processFiles}
              disabled={isProcessing || urlFiles.length === 0 || captionFiles.length === 0}
              className="flex-1 bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              <Upload className="w-5 h-5" />
              {isProcessing ? 'Memproses...' : 'Proses & Tampilkan Tabel'}
            </button>

            <button
              onClick={exportToExcel}
              disabled={tableData.length === 0}
              className="bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              Export Excel
            </button>
          </div>
        </div>

        {/* Table */}
        {tableData.length > 0 && (
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
            <div className="p-6 bg-indigo-600 text-white">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Calendar className="w-6 h-6" />
                Data Postingan ({tableData.length} item)
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 w-48">
                      Tanggal/Nama File
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      URL Postingan
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Caption
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {tableData.map((row, index) => (
                    <tr key={index} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 text-sm text-gray-700 font-medium">
                        {row.tanggal}
                      </td>
                      <td className="px-6 py-4 text-sm text-blue-600">
                        {row.url !== '-' ? (
                          <a href={row.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                            {row.url}
                          </a>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        <div className="max-h-32 overflow-y-auto whitespace-pre-wrap">
                          {row.caption}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}