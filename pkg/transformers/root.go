package transformers

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
)

// A simple struct to represent a file entry.
type FileEntry struct {
	// The path of the file relative to the root folder.
	Filename string
	// The size of the file in bytes.
	Filesize int64
}

// Walks through files in `rootFolder` and returns array of file entries.
func walkFiles(rootFolder string) ([]FileEntry, error) {
	var files []FileEntry

	err := filepath.Walk(rootFolder, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() {
			relPath, err := filepath.Rel(rootFolder, path)
			if err != nil {
				return err
			}

			files = append(files, FileEntry{
				Filename: relPath,
				Filesize: info.Size(),
			})
		}

		return nil
	})
	if err != nil {
		return nil, errors.New(fmt.Sprintf("error walking through files: %s", err))
	}

	return files, nil
}

// A simple XOR function that applies a key to the data (used in MHK Extra).
func xorData(data []byte, key []byte) []byte {
	keyLength := len(key)
	for i := range data {
		data[i] ^= key[i%keyLength]
	}
	return data
}

// Dynamically determines the appropriate (un)packing function based on the game ID.
// Action can either be `pack` or `unpack`.
func Transform(action string, gameId string, dataFileLocation string, rootFolder string) error {
	var transformFunction func(string, string, string) error

	switch gameId {
	case "mhk_extra":
		transformFunction = transformMhk1
	case "mhk_2":
		transformFunction = transformMhk2
	case "mhk_3":
		transformFunction = transformMhk3
	case "mhk_4":
		transformFunction = transformMhk4
	default:
		return errors.New("Invalid game ID")
	}

	var err error
	err = transformFunction(action, dataFileLocation, rootFolder)

	if err != nil {
		return errors.New(fmt.Sprintf("Error transforming data: %s", err))
	}

	return nil
}
