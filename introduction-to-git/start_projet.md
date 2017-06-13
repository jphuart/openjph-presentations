# Démarrer un projet

Commencer par créer le repository distant sur la plateforme choisie
(framagit, github, bitbucket, ...).

## Créer depuis le repository

	cd parent folder
	git clone git@framagit.org:openjph/test.git

## Créer depuis son pc

	cd existing_folder
	git init
	git remote add origin git@framagit.org:openjph/test.git
	git add .
	git commit -m "creation du depot"
	git push origin master