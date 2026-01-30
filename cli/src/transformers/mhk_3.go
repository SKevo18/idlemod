// "MHK 3 is almost the same format [as MHK 4], just the index is stored before the data.
// And the file offset is relative to the beginning of the data blob, not the sar file offset."
// - pyramidensurfer
package transformers

import (
	"encoding/binary"
	"errors"
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/text/encoding/charmap"
)

// Packs MHK 3 data files.
func packMhk3(dataFileLocation string, inputFolder string) error {
	dataFile, err := os.Create(dataFileLocation)
	if err != nil {
		return err
	}
	defer dataFile.Close()

	// read input folder
	fileEntries, err := walkFiles(inputFolder)
	if err != nil {
		return err
	}

	// write header
	dataFile.Seek(0, io.SeekStart)
	dataFile.Write([]byte("SARC2\x00\x00\x00"))
	filesCount := uint32(len(fileEntries))
	binary.Write(dataFile, binary.LittleEndian, filesCount)

	var relativeDataOffset uint32 = 0
	for _, fileEntry := range fileEntries {
		// write filename
		filename := strings.ReplaceAll(fileEntry.FilePath, "/", "\\")
		filename = strings.Replace(filename, "\\", ":\\", 1)

		// encode filename from UTF-8 to Windows-1252
		encodedFilename, err := charmap.Windows1252.NewEncoder().Bytes([]byte(filename))
		if err != nil {
			return err
		}

		filenameLength := uint8(len(encodedFilename))
		binary.Write(dataFile, binary.LittleEndian, filenameLength)
		dataFile.Write(encodedFilename)
		dataFile.Write([]byte{0x0})

		// get file size
		fileContent, _ := os.ReadFile(filepath.Join(inputFolder, fileEntry.FilePath))
		fileSize := len(fileContent)

		// offset and sizes
		binary.Write(dataFile, binary.LittleEndian, relativeDataOffset)
		binary.Write(dataFile, binary.LittleEndian, uint32(fileSize))
		binary.Write(dataFile, binary.LittleEndian, uint32(fileSize)) // file size is written twice

		relativeDataOffset += uint32(fileSize)
	}

	// Write file contents
	for _, entry := range fileEntries {
		fileContent, _ := os.ReadFile(filepath.Join(inputFolder, entry.FilePath))
		dataFile.Write(fileContent)
		log.Printf("Wrote `%s`", entry.FilePath)
	}

	log.Printf("Pack complete: %d files packed.", filesCount)
	return nil
}

// Unpacks MHK 3 data files.
func unpackMhk3(dataFileLocation string, outputDirectory string) error {
	dataFile, err := os.Open(dataFileLocation)
	if err != nil {
		return err
	}
	defer dataFile.Close()

	// header
	dataFileType := make([]byte, 0x8)
	dataFile.Read(dataFileType)
	log.Printf("Data file type: %s;", dataFileType)

	// read file count
	var fileCount uint32
	binary.Read(dataFile, binary.LittleEndian, &fileCount)
	log.Printf("File count: %d", fileCount)

	// read file entries
	unpackedFilesCount := 0
	fileEntries := make([]FileEntry, fileCount)
	log.Printf("Reading file entries...")
	for i := 0; i < int(fileCount); i++ {
		// read filename
		var filenameLength uint8
		binary.Read(dataFile, binary.LittleEndian, &filenameLength)
		filenameBytes := make([]byte, filenameLength)
		dataFile.Read(filenameBytes)

		dataFile.Seek(0x1, io.SeekCurrent) // skip null byte after filename

		// get file offset and length
		var fileOffset, fileLength uint32
		binary.Read(dataFile, binary.LittleEndian, &fileOffset)
		binary.Read(dataFile, binary.LittleEndian, &fileLength)

		// skip 4 bytes, file length is written twice
		dataFile.Seek(0x4, io.SeekCurrent)

		// decode filename from Windows-1252 to UTF-8
		decodedFilename, err := charmap.Windows1252.NewDecoder().Bytes(filenameBytes)
		if err != nil {
			return err
		}

		fileEntries[i] = FileEntry{
			FilePath:      string(decodedFilename),
			ContentOffset: int64(fileOffset),
			FileSize:      int64(fileLength),
		}
		log.Printf("Filename: %s; Offset: %d; Size: %d", fileEntries[i].FilePath, fileEntries[i].ContentOffset, fileEntries[i].FileSize)
	}

	dataStart, _ := dataFile.Seek(0, io.SeekCurrent)
	for _, entry := range fileEntries {
		// make parent dir for file
		filename := strings.ReplaceAll(entry.FilePath, ":", "")
		filename = strings.ReplaceAll(filename, "\\", "/")
		outputDirectory := filepath.Join(outputDirectory, filepath.Dir(filename))
		if err := os.MkdirAll(outputDirectory, os.ModePerm); err != nil {
			return err
		}
		outputPath := filepath.Join(outputDirectory, filepath.Base(filename))

		// offset of the next file entry
		nextOffset, _ := dataFile.Seek(0x4, io.SeekCurrent)

		// write file
		dataFile.Seek(dataStart+entry.ContentOffset, io.SeekStart)
		outputFile, err := os.Create(outputPath)
		if err != nil {
			return err
		}
		if _, err := io.CopyN(outputFile, dataFile, entry.FileSize); err != nil {
			return err
		}
		outputFile.Close()
		unpackedFilesCount++

		// go to next file
		dataFile.Seek(nextOffset, io.SeekStart)
		log.Printf("Filename: %s; Offset: %d; Size: %d", filename, entry.ContentOffset, entry.FileSize)
	}

	log.Printf("Unpack complete: %d/%d.", unpackedFilesCount, fileCount)
	return nil
}

func transformMhk3(action string, args []string) error {
	switch action {
	case "pack":
		return packMhk3(args[0], args[1])
	case "unpack":
		return unpackMhk3(args[0], args[1])
	default:
		return errors.New("invalid action")
	}
}
