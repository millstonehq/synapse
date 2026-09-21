package store

// Thing is the stored entity.
type Thing struct {
	ID int
}

// Repo is what a handler is handed: the dispatch through it is dynamic.
type Repo interface {
	Fetch(id int) Thing
}

// SQL is the storage-backed implementation.
type SQL struct{}

// Fetch reads one row of the things table.
func (s *SQL) Fetch(id int) Thing {
	return query(id)
}

// Memory is a second implementation that touches no store.
type Memory struct{}

// Fetch answers from memory and reads nothing.
func (m *Memory) Fetch(id int) Thing {
	return Thing{ID: id}
}

func query(id int) Thing { return Thing{ID: id} }
