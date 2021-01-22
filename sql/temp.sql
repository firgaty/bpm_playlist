SELECT main.library.id,
	main.library.path,
	main.library.title,
	main.library.albumartist,
	main.library.artist,
	main.library.composer,
	main.library.artistsort,
	main.library.album,
	database2.library.bpm,
	main.library.length,
	main.library.year
FROM main.library
JOIN database2.library
ON main.library.path = database2.library.path
