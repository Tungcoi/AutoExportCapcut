from auto import make_log_dir, click_on_project_by_name


if __name__ == "__main__":
    log_dir = make_log_dir()
    click_on_project_by_name("270TBN", log_dir)