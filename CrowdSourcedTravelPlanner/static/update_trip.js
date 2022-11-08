$(document).ready(function () {
    $(document).on('click','.add-exp-button', function() {
        // Get the parent article containing the experience information.
        var experience_identifier = $(this).attr('id');
        var experience_article = $('.' + experience_identifier);
        var trip_experience_container = $('#trip-experiences-div');

        // Update the "Add Trip" button to "Remove Trip"
        $(this).removeClass('add-exp-button');
        $(this).removeClass('btn-primary');
        $(this).addClass('remove-exp-button');
        $(this).addClass('btn-danger');
        $(this).text('Remove from trip');

        // Clone the experience to my trip.
        experience_article.clone().appendTo(trip_experience_container);

        // Remove the experience from search.
        experience_article.remove();

        // Obtain trip + experience IDs for database writing.
        var expID = experience_identifier.split("-").pop();
        var tripID = $('#trip-id').text();

        // POST request to add experience to trip.
        $.post( "/add_experience_to_trip",
                {"expID" : expID, "tripID" : tripID}
              );
    });

    $(document).on('click','.remove-exp-button', function() {
        // Get the parent article containing the experience information.
        var experience_identifier = $(this).attr('id');
        var experience_article = $('.' + experience_identifier);
        var search_experience_container = $('#search-experiences-div');

        // Update the "Add Trip" button to "Remove Trip"
        $(this).removeClass('remove-exp-button');
        $(this).removeClass('btn-danger');
        $(this).addClass('add-exp-button');
        $(this).addClass('btn-primary');
        $(this).text('Add to trip');

        // Clone the experience to my trip if it matches current search.
        var search_string = $('#search_string').val().toLowerCase();
        var exp_location = $('#' + experience_identifier +'-location').text().toLowerCase();
        if (search_string != "" && exp_location.indexOf(search_string) >= 0) {
            experience_article.clone().appendTo(search_experience_container);
        }

        // Remove the experience from search.
        experience_article.remove();

        // Obtain trip + experience IDs for database deleting.
        var expID = experience_identifier.split("-").pop();
        var tripID = $('#trip-id').text();

        // POST request to remove experience from trip.
        $.post( "/delete_experience_from_trip",
                {"expID" : expID, "tripID" : tripID}
              );
    });


});


